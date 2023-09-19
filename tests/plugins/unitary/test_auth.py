#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import os
from unittest.mock import MagicMock, patch
from oci_mlflow.auth_plugin import OCIMLFlowAuthRequestProvider


class TestOCIMLFlowAuth:
    def test_get_name(self):
        provider = OCIMLFlowAuthRequestProvider()
        assert provider.get_name() == "OCI_REQUEST_AUTH"

    @patch("oci_mlflow.auth_plugin.get_resource_principals_signer")
    @patch.dict(os.environ, {"OCI_IAM_TYPE": "resource_principal"})
    def test_get_auth_resource_principal(self, mock_get_signer):
        mock_get_signer.return_value = MagicMock()
        provider = OCIMLFlowAuthRequestProvider()
        auth = provider.get_auth()
        mock_get_signer.assert_called()
        assert auth == mock_get_signer.return_value

    @patch("oci_mlflow.auth_plugin.InstancePrincipalsSecurityTokenSigner")
    @patch.dict(os.environ, {"OCI_IAM_TYPE": "instance_principal"})
    def test_get_auth_instance_principal(self, mock_get_signer):
        mock_get_signer.return_value = MagicMock()
        provider = OCIMLFlowAuthRequestProvider()
        auth = provider.get_auth()
        assert auth == mock_get_signer.return_value
        mock_get_signer.assert_called()

    @patch("oci_mlflow.auth_plugin.SecurityTokenSigner")
    @patch("oci.signer.load_private_key_from_file")
    @patch("oci_mlflow.auth_plugin.utils._read_security_token_file")
    @patch("oci_mlflow.auth_plugin.from_file")
    @patch.dict(os.environ, {"OCI_IAM_TYPE": "security_token"})
    def test_get_auth_security_token(
        self,
        mock_from_config,
        mock_read_security_token_file,
        mock_load_private_key,
        mock_get_signer
    ):
        mock_from_config.return_value = {
            "fingerprint": "123",
            "key_file": "oci_api_key.pem",
            "tenancy": "test_tenancy",
            "region": "us-ashburn-1",
            "security_token_file": "token"
        }
        mock_read_security_token_file.return_value = "token"
        mock_load_private_key.return_value = MagicMock()
        mock_get_signer.return_value = MagicMock()
        provider = OCIMLFlowAuthRequestProvider()
        auth = provider.get_auth()
        assert auth == mock_get_signer.return_value
        mock_from_config.assert_called_with(
            file_location="~/.oci/config",
            profile_name="DEFAULT"
        )
        mock_read_security_token_file.assert_called_with(
            "token"
        )
        mock_load_private_key.assert_called_with(
            filename="oci_api_key.pem", 
            pass_phrase=None
        )
        mock_get_signer.assert_called()

    @patch("oci_mlflow.auth_plugin.Signer")
    @patch("oci_mlflow.auth_plugin.from_file")
    @patch.dict(os.environ, {"OCI_IAM_TYPE": "api_key"})
    def test_get_auth_api_key(self, mock_from_config, mock_signer):
        mock_from_config.return_value = {
            "fingerprint": "123",
            "key_file": "oci_api_key.pem",
            "tenancy": "test_tenancy",
            "region": "us-ashburn-1",
            "user": "test_user"
        }
        mock_signer.return_value = MagicMock()
        provider = OCIMLFlowAuthRequestProvider()
        auth = provider.get_auth()
        assert auth == mock_signer.return_value
        mock_from_config.assert_called_with(
            file_location="~/.oci/config",
            profile_name="DEFAULT"
        )
        mock_signer.assert_called_with(
            tenancy="test_tenancy",
            user="test_user",
            fingerprint="123",
            private_key_file_location="oci_api_key.pem",
            pass_phrase=None
        )

    @patch("oci_mlflow.auth_plugin.Signer")
    @patch("oci_mlflow.auth_plugin.from_file")
    @patch.dict(os.environ, {"OCI_IAM_TYPE": "invalid_type"})
    def test_get_auth_invalid_type(self, mock_from_config, mock_signer):
        mock_from_config.return_value = {
            "fingerprint": "123",
            "key_file": "oci_api_key.pem",
            "tenancy": "test_tenancy",
            "region": "us-ashburn-1",
            "user": "test_user"
        }
        mock_signer.return_value = MagicMock()
        provider = OCIMLFlowAuthRequestProvider()
        auth = provider.get_auth()
        assert auth == mock_signer.return_value
        mock_from_config.assert_called_with(
            file_location="~/.oci/config",
            profile_name="DEFAULT"
        )
        mock_signer.assert_called_with(
            tenancy="test_tenancy",
            user="test_user",
            fingerprint="123",
            private_key_file_location="oci_api_key.pem",
            pass_phrase=None
        )
