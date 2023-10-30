#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
from unittest.mock import patch
from oci_mlflow.auth_plugin import OCIMLFlowAuthRequestProvider


class TestOCIMLFlowAuth:
    def test_get_name(self):
        provider = OCIMLFlowAuthRequestProvider()
        assert provider.get_name() == "OCI_REQUEST_AUTH"

    @patch("oci_mlflow.auth_plugin.default_signer")
    def test_get_auth(self, mock_default_signer):
        mock_default_signer.return_value = {
            "config": {},
            "signer": "test_default_signer",
            "client_kwargs": {},
        }
        provider = OCIMLFlowAuthRequestProvider()
        auth = provider.get_auth()
        assert auth == "test_default_signer"
