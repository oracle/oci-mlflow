#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import json
import logging
import os

logger = logging.getLogger("oci.mlflow")
logger.setLevel(logging.INFO)

__version__ = ""
with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")
) as version_file:
    __version__ = json.load(version_file)["version"]


def setup_default_auth():
    if not os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
        os.environ["OCIFS_IAM_TYPE"] = "api_key"


if not ("OCIFS_IAM_TYPE" in os.environ or "OCI_IAM_TYPE" in os.environ):
    setup_default_auth()
elif os.environ.get("OCIFS_IAM_TYPE"):
    os.environ["OCI_IAM_TYPE"] = os.environ.get("OCIFS_IAM_TYPE")
elif os.environ.get("OCI_IAM_TYPE"):
    os.environ["OCIFS_IAM_TYPE"] = os.environ.get("OCI_IAM_TYPE")
