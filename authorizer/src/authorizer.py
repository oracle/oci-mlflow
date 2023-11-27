#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import io
import json
import logging
import copy

import fdk.response
from fdk import context, response

from authorizer.src.utils.identity_utils import (
    ExtendedIdentityDataPlaneClient,
    AuthenticationException,
    AuthorizationException
)

from authorizer.src.utils.auth_utils import (
    get_signer,
    SignerType,
    do_authn,
    do_authz,
    get_group_ids_from_config
)

from authorizer.src.utils.header_utils import (
    extract_and_validate_headers,
    AuthorizationHeaderMissingException,
    MissingRequiredHeadersException
)

logger = logging.getLogger(__name__)

# Initialising here so that this call is cached for future fn executions
identity_client = ExtendedIdentityDataPlaneClient(
    config={}, 
    signer=get_signer(SignerType.AUTO)
)

# The rest api methods currently supported by mlflow
# https://mlflow.org/docs/latest/rest-api.html
MLFLOW_REST_API_METHODS = ["post", "get", "delete", "patch", "put"]


def authorizer(ctx: context.InvokeContext, data: io.BytesIO = None) -> fdk.response.Response:
    """Performs authn and authz for given data.

    Parameters
    ----------
    ctx: InvokeContext
        An instance of InvokeContext.
    data: BytesIO
        Data in BytesIO format.

    Returns
    -------
    Response
        An instance of Response.
    """
    try:
        headers = extract_and_validate_headers(data.getvalue())
    except (
        AuthorizationHeaderMissingException, 
        MissingRequiredHeadersException
    ):
        return response.Response(
            ctx, status_code=401, response_data=json.dumps(
                {
                    "active": False,
                    "wwwAuthenticate": "Signature"
                }
            )
        )
    path_segment = copy.deepcopy(headers["(request-target)"])
    principal = None
    for method in MLFLOW_REST_API_METHODS:
        headers["(request-target)"] = [method + " " + path_segment[0]]
        try:
            principal = do_authn(identity_client, headers)
        except AuthenticationException:
            pass

    if principal:
        try:
            do_authz(
                identity_client, 
                principal, 
                get_group_ids_from_config(ctx.Config())
            )
                
            return response.Response(
                ctx, status_code=200, response_data=json.dumps(
                    {
                        "active": True,
                        "context": {
                            "subjectId": principal.subject_id
                        }
                    }
                )
            )
        except AuthorizationException as ex:
            logger.error('Error occurred while performing authZ: %s', str(ex))
    
    return response.Response(
        ctx, status_code=401, response_data=json.dumps(
            {
                "active": False,
                "wwwAuthenticate": "Signature"
            }
        )
    )
