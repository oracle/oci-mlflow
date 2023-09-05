import io
import json
import logging
import copy

import fdk.response
from fdk import context, response

from utils import auth_utils, header_utils, idc_utils

# Initialising here so that this call is cached for future fn executions
idc = idc_utils.ExtendedIdentityDataPlaneClient(config={}, signer=auth_utils.get_signer(
    auth_utils.SignerType.AUTO))

# The rest api methods currently supported by mlflow
# https://mlflow.org/docs/latest/rest-api.html
MLFLOW_REST_API_METHODS = ["get", "post", "delete", "patch"]


def authorizer(ctx: context.InvokeContext, data: io.BytesIO = None) -> fdk.response.Response:
    try:
        headers = header_utils.extract_and_validate_headers(data.getvalue())
    except (
        header_utils.AuthorizationHeaderMissingException, 
        header_utils.MissingRequiredHeadersException
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
            principal = auth_utils.do_authn(idc, headers)
        except idc_utils.AuthenticationException:
            pass

    if principal:
        try:
            auth_utils.do_authz(idc, principal, auth_utils.get_group_ids_from_config(ctx.Config()))
                
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
        except idc_utils.AuthorizationException as ex:
            logging.getLogger().error('Error occurred while performing authZ: %s', str(ex))
    
    return response.Response(
        ctx, status_code=401, response_data=json.dumps(
            {
                "active": False,
                "wwwAuthenticate": "Signature"
            }
        )
    )
