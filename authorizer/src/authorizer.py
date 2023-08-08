import io
import json
import logging

import fdk.response
from fdk import context, response

from utils import auth_utils, header_utils, idc_utils

# Initialising here so that this call is cached for future fn executions
idc = idc_utils.ExtendedIdentityDataPlaneClient(config={}, signer=auth_utils.get_signer(
    auth_utils.SignerType.AUTO))


def authorizer(ctx: context.InvokeContext, data: io.BytesIO = None) -> fdk.response.Response:
    try:
        principal = auth_utils.do_authn(idc, header_utils.extract_and_validate_headers(data.getvalue()))
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

    except Exception as ex:
        logging.getLogger().error('Error occurred while performing authN/authZ: %s', str(ex))
        return response.Response(
            ctx, status_code=401, response_data=json.dumps(
                {
                    "active": False,
                    "wwwAuthenticate": "Signature"
                }
            )
        )
