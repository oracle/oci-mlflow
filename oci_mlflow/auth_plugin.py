#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from ads.common.auth import default_signer
from mlflow.tracking.request_auth.abstract_request_auth_provider import RequestAuthProvider

OCI_REQUEST_AUTH = "OCI_REQUEST_AUTH"


class OCIMLFlowAuthRequestProvider(RequestAuthProvider):
    
    def get_name(self):
        """
        Get the name of the request auth provider.

        :return: str of request auth name
        """
        return OCI_REQUEST_AUTH

    def get_auth(self):
        """
        Generate oci signer based on oci environment variable.

        :return: OCI MLFlow signer
        """
        return default_signer()["signer"]
