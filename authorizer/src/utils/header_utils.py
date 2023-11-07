#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import json
from typing import Dict, List
from urllib import request

HEADERS_JSON_KEY = "data"
AUTHORIZATION_KEY = "authorization"
SIGNATURE_HEADERS_KEY = "headers"


class MissingRequiredHeadersException(Exception):
    def __init__(
        self, 
        required_headers: List[str], 
        provided_headers: List[str]
    ):
        self.required_headers = required_headers
        self.provided_headers = provided_headers

    def __str__(self):
        return "Headers required for authentication were not provided.\nProvided headers: {0}\nRequired headers: {1} \
            \nMissing headers: {2}".format(self.provided_headers, self.required_headers, set(self.required_headers)
                                           .difference(set(self.provided_headers)))


class AuthorizationHeaderMissingException(Exception):
    def __str__(self):
        return "Expected authorization header to be present but was not found"


class AuthorizationSigningHeadersMissingException(Exception):
    def __str__(self):
        return "Headers used to sign request was not present in authorization header"


def extract_and_validate_headers(data: bytes) -> Dict[str, List[str]]:
    """ Extracts headers from json document passed by APIGW and outputs in format required
    by authenticate client api

    input: {
        "type": "USER_DEFINED",
        "data": {
            "<argument-n>": "<context-variable-value>",
            "<argument-n>": "<context-variable-value>",
            "<argument-n>": "<context-variable-value>"
            }
        }
    output: {
        "<argument-n>" : [<context-variable-value>],
        "<argument-n>": [<context-variable-value>]
    }

    Parameters
    ----------
    data: bytes
        Input data in bytes.

    Returns
    -------
    Dict:
        A string-list dict.
    """
    headers = json.loads(data).get(HEADERS_JSON_KEY)
    headers = {str.lower(k): [v] for k, v in headers.items()}
    if not headers.get("date") and headers.get("x-date"):
        headers["date"] = headers["x-date"]
    try:
        required_headers = _get_required_headers_from_signature(headers.get(AUTHORIZATION_KEY)[0])
    except TypeError:
        raise AuthorizationHeaderMissingException()
    try:
        return {key: headers[key] for key in required_headers}
    except KeyError:
        raise MissingRequiredHeadersException(required_headers, provided_headers=list(headers.keys()))


def _get_required_headers_from_signature(auth_header: str) -> List[str]:
    """Extracts  headers required to validate from authorization header:
    
    input: 'Signature algorithm="rsa-sha256", headers="date (request-target) host",keyId="<keyid>",
            signature="<signature>"'
    output: ['date', '(request-target)', 'host', 'authorization']
    
    Parameters
    ----------
    auth_header: str
        The auth header string.

    Returns
    -------
    List:
        A list of headers from auth string.
    """
    kv = request.parse_keqv_list(request.parse_http_list(auth_header))
    signing_headers = kv.get(SIGNATURE_HEADERS_KEY)
    if signing_headers is None:
        raise AuthorizationSigningHeadersMissingException()
    required_headers = signing_headers.split(" ")
    required_headers.append(AUTHORIZATION_KEY)
    return list(map(str.lower, required_headers))
