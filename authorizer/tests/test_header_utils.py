#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import json
from unittest.mock import MagicMock, patch

import pytest

from authorizer.src.utils.header_utils import (
    AuthorizationHeaderMissingException,
    AuthorizationSigningHeadersMissingException,
    MissingRequiredHeadersException,
    _get_required_headers_from_signature,
    extract_and_validate_headers
)


def generate_apigw_json_payload(headers: dict) -> bytes:
    headers = {k.lower(): v for k, v in headers.items()}
    pl = {"type": "USER_DEFINED",
          "data": headers}
    return bytes(json.dumps(pl), 'utf-8')

@patch('authorizer.src.utils.header_utils._get_required_headers_from_signature')
def test_extract_validate_headers_pass(_get_required_headers_from_signature: MagicMock):
    headers = {"FoO": "test", "method": "get", "authorization": "authz"}
    expected_response = {"foo": ["test"]}
    _get_required_headers_from_signature.return_value = ["foo"]
    assert (extract_and_validate_headers(generate_apigw_json_payload(headers)) == expected_response)
    _get_required_headers_from_signature.assert_called_once_with("authz")

def test_extract_validate_headers_missing_authz():
    headers = {"FoO": "test", "method": "get"}
    with pytest.raises(AuthorizationHeaderMissingException):
        extract_and_validate_headers(generate_apigw_json_payload(headers))

@patch('authorizer.src.utils.header_utils._get_required_headers_from_signature')
def test_extract_validate_headers_missing_headers(_get_required_headers_from_signature: MagicMock):
    headers = {"FoO": "test", "method": "get", "authorization": "authz"}
    _get_required_headers_from_signature.return_value = ["foo1"]

    with pytest.raises(MissingRequiredHeadersException):
        extract_and_validate_headers(generate_apigw_json_payload(headers))
    _get_required_headers_from_signature.assert_called_once_with("authz")

def test_get_required_headers_from_signature_pass():
    authz_header = 'Signature algorithm="rsa-sha256", headers="Date (request-target) host", signature="<signature>"'
    expected_resp = ["date", "(request-target)", "host", "authorization"]
    assert (_get_required_headers_from_signature(authz_header) == expected_resp)

def test_get_required_headers_from_signature_fail():
    authz_header = 'Signature algorithm="rsa-sha256", signature="<signature>"'
    with pytest.raises(AuthorizationSigningHeadersMissingException):
        _get_required_headers_from_signature(authz_header)
