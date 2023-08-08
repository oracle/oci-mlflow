from typing import List

import oci
import six
from oci import retry


class ExtendedIdentityDataPlaneClient(oci.identity_data_plane.DataplaneClient):
    """
        Identity Dataplane Client with additional API support
    """

    def authenticate_client(self,
                            authenticate_client_details: oci.identity_data_plane.models.AuthenticateClientDetails,
                            **kwargs) -> oci.response.Response:  # pragma: no cover
        resource_path = "/authentication/authenticateClient"
        method = "POST"
        operation_name = "authenticate_client"
        api_reference_link = ""
        expected_kwargs = ["retry_strategy"]
        extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
        if extra_kwargs:
            raise ValueError(
                "authenticate_client got unknown kwargs: {!r}".format(extra_kwargs))

        header_params = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        retry_strategy = self.base_client.get_preferred_retry_strategy(
            operation_retry_strategy=kwargs.get('retry_strategy'),
            client_retry_strategy=self.retry_strategy
        )

        if retry_strategy:
            if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                self.base_client.add_opc_client_retries_header(header_params)
                retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
            return retry_strategy.make_retrying_call(
                self.base_client.call_api,
                resource_path=resource_path,
                method=method,
                header_params=header_params,
                body=authenticate_client_details,
                response_type="AuthenticateClientResult",
                allow_control_chars=None,
                operation_name=operation_name,
                api_reference_link=api_reference_link)
        else:
            return self.base_client.call_api(
                resource_path=resource_path,
                method=method,
                header_params=header_params,
                body=authenticate_client_details,
                response_type="AuthenticateClientResult",
                allow_control_chars=None,
                operation_name=operation_name,
                api_reference_link=api_reference_link)

    def filter_group_membership(self,
                                filter_membership_details: oci.identity_data_plane.models.FilterGroupMembershipDetails,
                                **kwargs) -> oci.response.Response:  # pragma: no cover
        resource_path = "/filterGroupMembership"
        method = "POST"
        operation_name = "filter_group_membership"
        api_reference_link = ""
        expected_kwargs = ["retry_strategy"]

        extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
        if extra_kwargs:
            raise ValueError(
                "filter_group_membership got unknown kwargs: {!r}".format(extra_kwargs))

        header_params = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        retry_strategy = self.base_client.get_preferred_retry_strategy(
            operation_retry_strategy=kwargs.get('retry_strategy'),
            client_retry_strategy=self.retry_strategy
        )

        if retry_strategy:
            if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                self.base_client.add_opc_client_retries_header(header_params)
                retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
            return retry_strategy.make_retrying_call(
                self.base_client.call_api,
                resource_path=resource_path,
                method=method,
                header_params=header_params,
                body=filter_membership_details,
                response_type="FilterGroupMembershipResult",
                allow_control_chars=None,
                operation_name=operation_name,
                api_reference_link=api_reference_link)
        else:
            return self.base_client.call_api(
                resource_path=resource_path,
                method=method,
                header_params=header_params,
                body=filter_membership_details,
                response_type="FilterGroupMembershipResult",
                allow_control_chars=None,
                operation_name=operation_name,
                api_reference_link=api_reference_link)


class AuthenticationException(Exception):
    def __init__(self, status_code: int, error_msg: str):
        self.status_code = status_code
        self.error_msg = error_msg

    def __str__(self):
        return "Could not authenticate client: Status code: {0}, Error Message: {1}".format(
            self.status_code, self.error_msg)


class AuthorizationException(Exception):
    def __init__(self, status_code: int, expected_group_ids: List[str], subject: str):
        self.expected_group_ids = expected_group_ids
        self.status_code = status_code
        self.subject = subject

    def __str__(self):
        return "Could not authorize client: Status code: {0}, Expected subject: {1} to be part any of the following " \
               "groups:{2}".format(self.status_code, self.subject, self.expected_group_ids)
