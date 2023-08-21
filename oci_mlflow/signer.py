from oci import Signer
import os

from oci.auth.signers.resource_principals_federation_signer import ResourcePrincipalsFederationSigner
from oci.auth.signers.ephemeral_resource_principals_signer import EphemeralResourcePrincipalSigner
from oci.auth.signers.ephemeral_resource_principals_v21_signer import EphemeralResourcePrincipalV21Signer
from oci.auth.signers.instance_principals_security_token_signer import InstancePrincipalsSecurityTokenSigner

OCI_RESOURCE_PRINCIPAL_VERSION = "OCI_RESOURCE_PRINCIPAL_VERSION"
OCI_RESOURCE_PRINCIPAL_RPST = "OCI_RESOURCE_PRINCIPAL_RPST"
OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM = "OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM"
OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM_PASSPHRASE = "OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM_PASSPHRASE"
OCI_RESOURCE_PRINCIPAL_REGION = "OCI_RESOURCE_PRINCIPAL_REGION"
OCI_RESOURCE_PRINCIPAL_RPT_ENDPOINT = "OCI_RESOURCE_PRINCIPAL_RPT_ENDPOINT"
OCI_RESOURCE_PRINCIPAL_RPST_ENDPOINT = "OCI_RESOURCE_PRINCIPAL_RPST_ENDPOINT"
OCI_RESOURCE_PRINCIPAL_RESOURCE_ID = "OCI_RESOURCE_PRINCIPAL_RESOURCE_ID"
OCI_RESOURCE_PRINCIPAL_TENANCY_ID = "OCI_RESOURCE_PRINCIPAL_TENANCY_ID"

def get_resource_principals_signer(resource_principal_token_path_provider=None):
    """
    A Resource Principals signer is token based signer. The flavor of resource
    principals signer required is determined by the configured environment of
    the instance.

    returns: a resource principals signer
    """

    rp_version = os.environ.get(OCI_RESOURCE_PRINCIPAL_VERSION, "UNDEFINED")
    if rp_version == "2.2":
        """
        This signer takes its configuration from the following environment variables.
        - OCI_RESOURCE_PRINCIPAL_RPST: the Resource Principals Session Token
        - OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM: the private key in PEM format
        - OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM_PASSPHRASE: the (optional) passphrase for the private key

            These three variables may be used in one of two modes. In the first mode, they contain the actual
            contents of the RPST, private key (in PEM format) and the passphrase. This mode is only useful for
            short-lived programs.

            In the second mode, if these variables contain absolute paths, then those paths are taken as the
            on-filesystem location of the values in question. The signer may attempt to reload these values from
            the filesystem on receiving a 401 response from an OCI service. This mode is used in cases where the
            program executes in an environment where an external provider may inject updated tokens into
            the filesystem.

        - OCI_RESOURCE_PRINCIPAL_REGION: the canonical region name

            This is utilised in locating the "local" endpoints of services.
        """
        session_token = os.environ.get(OCI_RESOURCE_PRINCIPAL_RPST)
        private_key = os.environ.get(OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM)
        private_key_passphrase = os.environ.get(OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM_PASSPHRASE)
        region = os.environ.get(OCI_RESOURCE_PRINCIPAL_REGION)

        return OCIMLFlowSigner(
            session_token=session_token,
            private_key=private_key,
            private_key_passphrase=private_key_passphrase,
            region=region
        )

    elif rp_version in ["2.1", "2.1.1"]:
        """
        This signer takes its configuration from the following environment variables.
            - OCI_RESOURCE_PRINCIPAL_RPT_ENDPOINT: The endpoint for retrieving the Resource Principal Token
            - OCI_RESOURCE_PRINCIPAL_RPST_ENDPOINT: The endpoint for retrieving the Resource Principal Session Token
            - OCI_RESOURCE_PRINCIPAL_RESOURCE_ID: The RPv2.1/Rpv2.1.1 resource id
            - OCI_RESOURCE_PRINCIPAL_TENANCY_ID: The RPv2.1.1 tenancy id
            - OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM: The private key in PEM format
            - OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM_PASSPHRASE: The (optional) passphrase for the private key
        """
        resource_principal_token_endpoint = os.environ.get(OCI_RESOURCE_PRINCIPAL_RPT_ENDPOINT)
        resource_principal_session_token_endpoint = os.environ.get(OCI_RESOURCE_PRINCIPAL_RPST_ENDPOINT)
        resource_id = os.environ.get(OCI_RESOURCE_PRINCIPAL_RESOURCE_ID)
        tenancy_id = os.environ.get(OCI_RESOURCE_PRINCIPAL_TENANCY_ID)
        private_key = os.environ.get(OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM)
        private_key_passphrase = os.environ.get(OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM_PASSPHRASE)

        return OCIMLFlowSigner(
            resource_principal_token_endpoint=resource_principal_token_endpoint,
            resource_principal_session_token_endpoint=resource_principal_session_token_endpoint,
            resource_id=resource_id,
            tenancy_id=tenancy_id,
            private_key=private_key,
            private_key_passphrase=private_key_passphrase,
            rp_version=rp_version
        )

    elif rp_version == "1.1":
        """
        This signer takes its configuration from the following environement variables
        - OCI_RESOURCE_PRINCIPAL_RPT_ENDPOINT
            The endpoint for retreiving the Resource Principal Token
        - OCI_RESOURCE_PRINCIPAL_RPST_ENDPOINT
            The endpoint for retrieving the Resource Principal Session Token
        """
        resource_principal_token_endpoint = os.environ.get(OCI_RESOURCE_PRINCIPAL_RPT_ENDPOINT)
        resource_principal_session_token_endpoint = os.environ.get(OCI_RESOURCE_PRINCIPAL_RPST_ENDPOINT)

        return OCIMLFlowSigner(
            resource_principal_token_endpoint=resource_principal_token_endpoint,
            resource_principal_session_token_endpoint=resource_principal_session_token_endpoint,
            resource_principal_token_path_provider=resource_principal_token_path_provider
        )

    elif rp_version == "UNDEFINED":
        raise EnvironmentError("{} is not defined".format(OCI_RESOURCE_PRINCIPAL_VERSION))
    else:
        raise EnvironmentError("Unsupported {}: {}".format(OCI_RESOURCE_PRINCIPAL_VERSION, rp_version))

class OCIMLFlowSigner(
    Signer,
    EphemeralResourcePrincipalSigner,
    EphemeralResourcePrincipalV21Signer,
    ResourcePrincipalsFederationSigner,
    InstancePrincipalsSecurityTokenSigner
):
    def __init__(
        self,
        tenancy, 
        user, 
        fingerprint, 
        private_key_file_location, 
        pass_phrase=None, 
        private_key_content=None
    ):
        Signer(
            tenancy, 
            user, 
            fingerprint, 
            private_key_file_location, 
            pass_phrase, 
            private_key_content
        )

    def __init__(
        self, 
        session_token=None, 
        private_key=None, 
        private_key_passphrase=None, 
        region=None, 
        generic_headers=None, 
        **kwargs
    ):
        EphemeralResourcePrincipalSigner(
            session_token, 
            private_key, 
            private_key_passphrase, 
            region, 
            generic_headers, 
            **kwargs
        )

    def __init__(
        self, 
        resource_principal_token_endpoint=None, 
        resource_principal_session_token_endpoint=None, 
        resource_id=None, 
        private_key=None, 
        private_key_passphrase=None, 
        retry_strategy=None, 
        log_requests=None, 
        generic_headers=None, 
        tenancy_id=None, 
        rp_version=None, 
        **kwargs
    ):
        EphemeralResourcePrincipalV21Signer(
            resource_principal_token_endpoint, 
            resource_principal_session_token_endpoint, 
            resource_id, 
            private_key, 
            private_key_passphrase, 
            retry_strategy, 
            log_requests, 
            generic_headers, 
            tenancy_id, 
            rp_version, 
            **kwargs
        )
    
    def __init__(
        self, 
        resource_principal_token_endpoint=None, 
        resource_principal_session_token_endpoint=None, 
        resource_principal_token_path_provider=None, 
        retry_strategy=None, 
        log_requests=None, 
        generic_headers=None, 
        **kwargs
    ):
        ResourcePrincipalsFederationSigner(
            resource_principal_token_endpoint, 
            resource_principal_session_token_endpoint, 
            resource_principal_token_path_provider, 
            retry_strategy, 
            log_requests, 
            generic_headers, 
            **kwargs
        )

    def __init__(self, **kwargs):
        InstancePrincipalsSecurityTokenSigner(**kwargs)

    def do_request_sign(self, request, enforce_content_headers=True):
        """Override the do_request_sign method in oci.signer class
        https://github.com/oracle/oci-python-sdk/blob/master/src/oci/signer.py#L192 in to add `path` header. 
        `path` header is required for OCI Authorizer Function to authenticate request from IAM backend.

        Parameters
        ----------
        request:
            Outgoing http request object
        enforce_content_headers: bool
            Whether content headers should be added for PUT and POST requests when not present.

        Returns
        -------
        request:
            Outgoing http request object with `path` and signature headers added
        """
        request.headers.setdefault(
            "path", request.method.lower() + " " + request.path_url
        )
        return super().do_request_sign(
            request,
            enforce_content_headers=enforce_content_headers,
        )
