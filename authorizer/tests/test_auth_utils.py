#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import os
from unittest.mock import MagicMock, patch

import oci.identity_data_plane.models
import pytest

from authorizer.src.utils import auth_utils
from authorizer.src.utils.identity_utils import (
    AuthenticationException,
    ExtendedIdentityDataPlaneClient
)

MOCK_RET_VAL = "MOCK_RET_VAL"


@patch('authorizer.src.utils.auth_utils._get_internal_instance_principal_signer')
def test_get_ip_signer(get_ip_mock: MagicMock):
    get_ip_mock.return_value = MOCK_RET_VAL
    assert (
        auth_utils.get_signer(auth_utils.SignerType.INSTANCE_PRINCIPAL) == MOCK_RET_VAL
    )
    get_ip_mock.assert_called_once()

def test_get_group_ids():
    group_ids = auth_utils.get_group_ids_from_config({"GROUP_IDS": "id1,  id2, id3,    id4   "})
    assert group_ids == ["id1", "id2", "id3", "id4"]

@patch('authorizer.src.utils.auth_utils.get_resource_principals_signer')
def test_get_rp_signer(rp_signer_mock: MagicMock):
    rp_signer_mock.return_value = MOCK_RET_VAL
    assert (
        auth_utils.get_signer(auth_utils.SignerType.RESOURCE_PRINCIPAL) == MOCK_RET_VAL
    )
    rp_signer_mock.assert_called_once()

@patch('authorizer.src.utils.auth_utils._get_env_bool')
def test_auto_ip_signer(get_env_mock: MagicMock):
    os.environ["RP_AUTH"] = "false"
    get_env_mock.return_value = False
    with patch('authorizer.src.utils.auth_utils.InstancePrincipalsSecurityTokenSigner') as ip_signer_mock:
        auth_utils.get_signer(auth_utils.SignerType.AUTO)
        assert (
            auth_utils.get_signer(auth_utils.SignerType.AUTO) == ip_signer_mock.return_value
        )
        ip_signer_mock.assert_called()
    get_env_mock.assert_called_with("RP_AUTH", False)

@patch('authorizer.src.utils.auth_utils._get_env_bool')
@patch('authorizer.src.utils.auth_utils.get_resource_principals_signer')
def test_auto_rp_signer(rp_signer_mock: MagicMock, get_env_mock: MagicMock):
    os.environ["RP_AUTH"] = "true"
    rp_signer_mock.return_value = MOCK_RET_VAL
    get_env_mock.return_value = True
    assert (
        auth_utils.get_signer(auth_utils.SignerType.AUTO) == MOCK_RET_VAL
    )
    get_env_mock.assert_called_once_with("RP_AUTH", False)
    rp_signer_mock.assert_called_once()

@patch('authorizer.src.utils.auth_utils.InstancePrincipalsSecurityTokenSigner')
def test_get_internal_ip_signer(ip_signer_mock: MagicMock):
    ip_signer_mock.return_value = MOCK_RET_VAL
    test_override_url = "test"
    os.environ["METADATA_OVERRIDE_URL"] = test_override_url
    assert (
        auth_utils._get_internal_instance_principal_signer() == MOCK_RET_VAL
    )
    assert (
        ip_signer_mock.GET_REGION_URL == test_override_url + "/instance/region"
    )
    assert (
        ip_signer_mock.METADATA_URL_BASE == test_override_url
    )
    ip_signer_mock.assert_called_once()

def test_get_env_bool_val_error():
    os.environ["_test"] = "garbage"
    with pytest.raises(ValueError):
        auth_utils._get_env_bool("_test")

def test_get_env_bool_val_none():
    os.environ.pop('_test', None)
    assert (auth_utils._get_env_bool("_test", False) is False)
    assert (auth_utils._get_env_bool("_test", True) is True)

def test_get_env_bool_val_true():
    os.environ["_test"] = "tRuE"
    assert (auth_utils._get_env_bool("_test", False) is True)

def test_get_env_bool_val_false():
    os.environ["_test"] = "FALSe"
    assert (auth_utils._get_env_bool("_test", True) is False)

def test_do_authn_fail():
    authenticate_result = oci.identity_data_plane.models.AuthenticateClientResult()
    authenticate_result.principal = None
    authenticate_result.error_message = "authn failed"

    response = oci.response.Response(
        status=200,
        data=authenticate_result,
        headers=None,
        request=None
    )
    response.data = authenticate_result

    headers = {"foo": ["test"]}

    auth_client_details = oci.identity_data_plane.models.AuthenticateClientDetails()
    auth_client_details.request_headers = headers

    idc_mock = MagicMock(type=ExtendedIdentityDataPlaneClient)
    idc_mock.authenticate_client = MagicMock()
    idc_mock.authenticate_client.return_value = response
    with pytest.raises(AuthenticationException):
        auth_utils.do_authn(idc_mock, headers)

    idc_mock.authenticate_client.assert_called_once_with(
        authenticate_client_details=auth_client_details
    )

def test_do_authn_pass():
    authenticate_result = oci.identity_data_plane.models.AuthenticateClientResult()
    authenticate_result.principal = MOCK_RET_VAL
    authenticate_result.error_message = None

    response = oci.response.Response(
        status=200,
        data=authenticate_result,
        headers=None,
        request=None
    )

    headers = {"foo": ["test"]}

    auth_client_details = oci.identity_data_plane.models.AuthenticateClientDetails()
    auth_client_details.request_headers = headers

    idc_mock = MagicMock(type=ExtendedIdentityDataPlaneClient)
    idc_mock.authenticate_client = MagicMock()
    idc_mock.authenticate_client.return_value = response
    assert (
        auth_utils.do_authn(idc_mock, headers) == authenticate_result.principal
    )

    idc_mock.authenticate_client.assert_called_once_with(authenticate_client_details=auth_client_details)

def test_authz_pass():
    principal = oci.identity_data_plane.models.Principal()
    expected_group_ids = ["g1", "g3"]
    idc = MagicMock(type=ExtendedIdentityDataPlaneClient)
    idc.filter_group_membership = MagicMock()

    filter_group_membership_details = oci.identity_data_plane.models.FilterGroupMembershipDetails()
    filter_group_membership_details.principal = principal
    filter_group_membership_details.group_ids = expected_group_ids

    filter_group_membership_result = oci.identity_data_plane.models.FilterGroupMembershipResult()
    filter_group_membership_result.group_ids = ["g1"]
    filter_group_membership_result.principal = principal

    response = oci.response.Response(
        status=200,
        data=filter_group_membership_result,
        headers=None,
        request=None
    )
    idc.filter_group_membership.return_value = response

    assert (
        auth_utils.do_authz(idc, principal, expected_group_ids) == filter_group_membership_result.group_ids
    )
    idc.filter_group_membership.assert_called_once_with(filter_group_membership_details)

def test_authz_fail():
    principal = oci.identity_data_plane.models.Principal()
    expected_group_ids = ["g1", "g3"]
    idc = MagicMock(type=ExtendedIdentityDataPlaneClient)
    idc.filter_group_membership = MagicMock()

    filter_group_membership_details = oci.identity_data_plane.models.FilterGroupMembershipDetails()
    filter_group_membership_details.principal = principal
    filter_group_membership_details.group_ids = expected_group_ids

    filter_group_membership_result = oci.identity_data_plane.models.FilterGroupMembershipResult()
    filter_group_membership_result.group_ids = ["g2"]
    filter_group_membership_result.principal = principal

    response = oci.response.Response(
        status=401,
        data=filter_group_membership_result,
        headers=None,
        request=None
    )
    idc.filter_group_membership.return_value = response

    with pytest.raises(auth_utils.AuthorizationException):
        auth_utils.do_authz(idc, principal, expected_group_ids)
    idc.filter_group_membership.assert_called_once_with(filter_group_membership_details)
