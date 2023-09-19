from ads.common.auth import AuthType
#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from oci import Signer
from oci.auth.signers import (
    get_resource_principals_signer,
    InstancePrincipalsSecurityTokenSigner,
    SecurityTokenSigner
)
from oci.config import (
    from_file,
    DEFAULT_LOCATION, # "~/.oci/config"
    DEFAULT_PROFILE # "DEFAULT"
)
import os
import oci
from mlflow.tracking.request_auth.abstract_request_auth_provider import RequestAuthProvider


from oci_mlflow import logger, utils

OCI_REQUEST_AUTH = "OCI_REQUEST_AUTH"
OCIFS_IAM_TYPE = "OCIFS_IAM_TYPE"
OCI_IAM_TYPE = "OCI_IAM_TYPE"
OCI_CONFIG_PROFILE = "OCI_CONFIG_PROFILE"
OCI_CONFIG_LOCATION = "OCI_CONFIG_LOCATION"

class OCIMLFlowAuthRequestProvider(RequestAuthProvider):
    
    def get_name(self):
        """
        Get the name of the request auth provider.

        :return: str of request auth name
        """
        return OCI_REQUEST_AUTH

    def get_auth(self):
        """
        Generate context-specific request auth.

        :return: OCI MLFlow signer
        """
        auth_type = os.environ.get(OCI_IAM_TYPE) or os.environ.get(OCIFS_IAM_TYPE)
        file_location = os.environ.get(
            OCI_CONFIG_LOCATION, DEFAULT_LOCATION
        )
        profile_name = os.environ.get(
            OCI_CONFIG_PROFILE, DEFAULT_PROFILE
        )
        if auth_type == AuthType.RESOURCE_PRINCIPAL:
            return get_resource_principals_signer()
        elif auth_type == AuthType.INSTANCE_PRINCIPAL:
            return InstancePrincipalsSecurityTokenSigner()
        elif auth_type == AuthType.SECURITY_TOKEN:
            config = from_file(
                file_location=file_location,
                profile_name=profile_name
            )
            token=utils._read_security_token_file(
                config.get("security_token_file")
            )
            private_key=oci.signer.load_private_key_from_file(
                filename=config.get("key_file"), 
                pass_phrase=config.get("pass_phrase")
            )
            return SecurityTokenSigner(token=token, private_key=private_key)
        else:
            if auth_type != AuthType.API_KEY:
                logger.info("Invalid or empty auth type. Using api_key as default authentication.")
            config = from_file(
                file_location=file_location,
                profile_name=profile_name
            )
            return Signer(
                tenancy=config.get("tenancy"),
                user=config.get("user"),
                fingerprint=config.get("fingerprint"),
                private_key_file_location=config.get("key_file"),
                pass_phrase=config.get("pass_phrase")
            )
