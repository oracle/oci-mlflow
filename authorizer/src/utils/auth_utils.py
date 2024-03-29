#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import os
from enum import Enum
from typing import Dict, List

from oci.auth.signers import (
    InstancePrincipalsSecurityTokenSigner,
    get_resource_principals_signer
)
from oci.identity_data_plane.models import (
    AuthenticateClientDetails,
    AuthenticateClientResult,
    FilterGroupMembershipDetails,
    FilterGroupMembershipResult
)
from oci.identity_data_plane.models.principal import Principal

from authorizer.src.utils.identity_utils import (
    AuthenticationException,
    AuthorizationException,
    ExtendedIdentityDataPlaneClient
)

ALLOWED_GROUP_IDS = "GROUP_IDS"


class SignerType(Enum):
    AUTO = 0
    RESOURCE_PRINCIPAL = 1
    INSTANCE_PRINCIPAL = 2


def get_signer(signer_type: SignerType = SignerType.AUTO):
    """Gets the corresponding signer from signer type.

    Parameters
    ----------
    signer_type: integer
        The signer type

    Returns
    -------
    Signer:
        An instance of Signer.
    """
    if signer_type == SignerType.AUTO:
        if _get_env_bool("RP_AUTH", False):
            signer_type = SignerType.RESOURCE_PRINCIPAL
        else:
            signer_type = SignerType.INSTANCE_PRINCIPAL
    if signer_type == SignerType.RESOURCE_PRINCIPAL:
        return get_resource_principals_signer()
    else:
        return _get_internal_instance_principal_signer()


def do_authn(
    identity_client: ExtendedIdentityDataPlaneClient,
    headers: Dict[str, List[str]]
) -> Principal:
    """Performs the authn validation from given headers.

    Parameters
    ----------
    identity_client: ExtendedIdentityDataPlaneClient
        An instance of ExtendedIdentityDataPlaneClient
    headers: dict
        A dict of headers to be authenticated

    Returns
    -------
    Principal:
        An instance of Principal
    """
    client_details = AuthenticateClientDetails()
    client_details.request_headers = headers
    authenticate_response = identity_client.authenticate_client(authenticate_client_details=client_details)
    authenticate_result: AuthenticateClientResult = authenticate_response.data
    if authenticate_result.principal is None:
        raise AuthenticationException(authenticate_response.status, authenticate_result.error_message)
    return authenticate_result.principal


def do_authz(
    identity_client: ExtendedIdentityDataPlaneClient, 
    principal: Principal, 
    expected_group_ids: List[str]
) -> List[str]:
    """Performs the authz validation from principal and expected group ids.

    Parameters
    ----------
    identity_client: ExtendedIdentityDataPlaneClient
        An instance of ExtendedIdentityDataPlaneClient.
    principal: Principal
        An instance of Principal.
    expected_group_ids: list
        A list of allowed group ids.

    Returns
    -------
    List:
        A list of allowed group ids.
    """
    filter_group_membership_details = FilterGroupMembershipDetails()
    filter_group_membership_details.principal = principal
    filter_group_membership_details.group_ids = expected_group_ids
    membership_response = identity_client.filter_group_membership(filter_group_membership_details)
    membership_result: FilterGroupMembershipResult = membership_response.data
    if not set(expected_group_ids).intersection(membership_result.group_ids):
        raise AuthorizationException(membership_response.status, expected_group_ids, principal.subject_id)
    return membership_result.group_ids


def get_group_ids_from_config(config: Dict) -> List[str]:
    """Gets group ids from config.

    Parameters
    ----------
    config: dict
        A dict of configurations

    Returns
    -------
    List
        A list of group ids seperated in the original string by ','
    """
    return config.get(ALLOWED_GROUP_IDS, "").replace(" ", "").split(",")


def _get_internal_instance_principal_signer() -> InstancePrincipalsSecurityTokenSigner:
    """Overrides metadata url of InstancePrincipalSigner class"""
    override_metadata_url = os.getenv(
        "METADATA_OVERRIDE_URL",
        InstancePrincipalsSecurityTokenSigner.METADATA_URL_BASE
    )
    InstancePrincipalsSecurityTokenSigner.METADATA_URL_BASE = override_metadata_url
    InstancePrincipalsSecurityTokenSigner.GET_REGION_URL = \
        '{}/instance/region'.format(override_metadata_url)
    InstancePrincipalsSecurityTokenSigner.LEAF_CERTIFICATE_URL = \
        '{}/identity/cert.pem'.format(override_metadata_url)
    InstancePrincipalsSecurityTokenSigner.LEAF_CERTIFICATE_PRIVATE_KEY_URL = \
        '{}/identity/key.pem'.format(override_metadata_url)
    InstancePrincipalsSecurityTokenSigner.INTERMEDIATE_CERTIFICATE_URL = \
        '{}/identity/intermediate.pem'.format(override_metadata_url)
    return InstancePrincipalsSecurityTokenSigner()


def _get_env_bool(env_var: str, default: bool = False) -> bool:
    env_val = os.getenv(env_var)

    if env_val is None:
        return default

    return env_val.lower() in ("true","t","1")
