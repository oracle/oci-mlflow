import os
from enum import Enum
from typing import Dict, List

import oci.auth.signers
from oci.identity_data_plane.models import (AuthenticateClientDetails,
                                            AuthenticateClientResult,
                                            FilterGroupMembershipDetails,
                                            FilterGroupMembershipResult)
from oci.identity_data_plane.models.principal import Principal

from utils.idc_utils import (AuthenticationException, AuthorizationException,
                             ExtendedIdentityDataPlaneClient)


class SignerType(Enum):
    AUTO = 0
    RESOURCE_PRINCIPAL = 1
    INSTANCE_PRINCIPAL = 2

    # def __eq__(self, other):
    #     return self.value == other.value


def get_signer(signer_type: SignerType = SignerType.AUTO):
    if signer_type == SignerType.AUTO:
        if _get_env_bool("RP_AUTH", False):
            signer_type = SignerType.RESOURCE_PRINCIPAL
        else:
            signer_type = SignerType.INSTANCE_PRINCIPAL
    if signer_type == SignerType.RESOURCE_PRINCIPAL:
        return oci.auth.signers.get_resource_principals_signer()
    else:
        return _get_internal_instance_principal_signer()


def do_authn(idc: ExtendedIdentityDataPlaneClient, headers: Dict[str, List[str]]) -> Principal:
    client_details = AuthenticateClientDetails()
    client_details.request_headers = headers
    authenticate_response = idc.authenticate_client(authenticate_client_details=client_details)
    authenticate_result: AuthenticateClientResult = authenticate_response.data
    if authenticate_result.principal is None:
        raise AuthenticationException(authenticate_response.status, authenticate_result.error_message)
    return authenticate_result.principal


def do_authz(idc: ExtendedIdentityDataPlaneClient, principal: Principal, expected_group_ids: List[str]) -> List[str]:
    """
    :param idc: identity clients
    :param principal:
    :param expected_group_ids:
    :return:
    """
    filter_group_membership_details = FilterGroupMembershipDetails()
    filter_group_membership_details.principal = principal
    filter_group_membership_details.group_ids = expected_group_ids
    membership_response = idc.filter_group_membership(filter_group_membership_details)
    membership_result: FilterGroupMembershipResult = membership_response.data
    if not set(expected_group_ids).intersection(membership_result.group_ids):
        raise AuthorizationException(membership_response.status, expected_group_ids, principal.subject_id)
    return membership_result.group_ids


def get_group_ids_from_config(config: Dict) -> List[str]:
    """
    :param config: Dictionary of fn configuration variables
    :return: List of group ids seperated in the original string by ','
    """
    group_ids = config.get("GROUP_IDS")
    group_ids = group_ids.replace(" ", "")
    return group_ids.split(',')


def _get_internal_instance_principal_signer() -> oci.auth.signers.InstancePrincipalsSecurityTokenSigner:
    """Overrides metadata url of InstancePrincipalSigner class"""
    override_metadata_url = os.getenv("METADATA_OVERRIDE_URL",
                                      oci.auth.signers.InstancePrincipalsSecurityTokenSigner.METADATA_URL_BASE)
    oci.auth.signers.InstancePrincipalsSecurityTokenSigner.METADATA_URL_BASE = override_metadata_url
    oci.auth.signers.InstancePrincipalsSecurityTokenSigner.GET_REGION_URL = \
        '{}/instance/region'.format(override_metadata_url)
    oci.auth.signers.InstancePrincipalsSecurityTokenSigner.LEAF_CERTIFICATE_URL = \
        '{}/identity/cert.pem'.format(override_metadata_url)
    oci.auth.signers.InstancePrincipalsSecurityTokenSigner.LEAF_CERTIFICATE_PRIVATE_KEY_URL = \
        '{}/identity/key.pem'.format(override_metadata_url)
    oci.auth.signers.InstancePrincipalsSecurityTokenSigner.INTERMEDIATE_CERTIFICATE_URL = \
        '{}/identity/intermediate.pem'.format(override_metadata_url)
    return oci.auth.signers.InstancePrincipalsSecurityTokenSigner()


def _get_env_bool(env_var: str, default: bool = False) -> bool:
    """
    :param env_var: Environment variable name
    :param default: Default environment variable value
    :return: Value of the boolean env variable
    """
    env_val = os.getenv(env_var)
    if env_val is None:
        env_val = default
    else:
        env_val = env_val.lower()
        if env_val == "true":
            env_val = True
        elif env_val == "false":
            env_val = False
        else:
            raise ValueError("For environment variable: {0} only string values T/true or F/false are allowed but: \
                {1} was provided.".format(env_var, env_val))
    return env_val
