from oci.config import from_file
import os
from mlflow.tracking.request_auth.abstract_request_auth_provider import RequestAuthProvider
from oci_mlflow.signer import (
    OCIMLFlowSigner, 
    get_resource_principals_signer
)

from oci_mlflow import logger

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
        Generate context-specific request auth.

        :return: OCI MLFlow signer
        """
        auth_type = os.environ.get("OCIFS_IAM_TYPE")
        if auth_type == "resource_principal":
            return get_resource_principals_signer()
        elif auth_type == "instance_principal":
            return OCIMLFlowSigner()
        else:
            if auth_type != "api_key":
                logger.info("Invalid or empty auth type. Using api_key as default authentication.")
            config = from_file()
            return OCIMLFlowSigner(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config["key_file"],
                pass_phrase=config.get("pass_phrase")
            )
