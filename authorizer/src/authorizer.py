import io
import json
import logging
import copy

import fdk.response
from fdk import context, response

from utils.identity_utils import (
    ExtendedIdentityDataPlaneClient,
    AuthenticationException,
    AuthorizationException
)

from utils.auth_utils import (
    get_signer,
    SignerType,
    do_authn,
    do_authz,
    get_group_ids_from_config
)

from utils.header_utils import (
    extract_and_validate_headers,
    AuthorizationHeaderMissingException,
    MissingRequiredHeadersException
)

# Initialising here so that this call is cached for future fn executions
identity_client = ExtendedIdentityDataPlaneClient(
    config={}, 
    signer=get_signer(SignerType.AUTO)
)

# The rest api methods currently supported by mlflow
# https://mlflow.org/docs/latest/rest-api.html
MLFLOW_REST_API_METHODS = ["post", "get", "delete", "patch"]


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
            logging.getLogger().error('Error occurred while performing authZ: %s', str(ex))
    
    return response.Response(
        ctx, status_code=401, response_data=json.dumps(
            {
                "active": False,
                "wwwAuthenticate": "Signature"
            }
        )
    )
