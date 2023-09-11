#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import json
import logging
import os

logger = logging.getLogger("oci.mlflow")
logger.setLevel(logging.INFO)

# https://packaging.python.org/en/latest/guides/single-sourcing-package-version/#single-sourcing-the-package-version
from importlib import metadata

__version__ = metadata.version("oci_mlflow")


def setup_default_auth():
    """Setup default auth."""
    if os.environ.get("OCIFS_IAM_TYPE") and os.environ.get("OCI_IAM_TYPE"):
        return
    if os.environ.get("OCIFS_IAM_TYPE"):
        os.environ["OCI_IAM_TYPE"] = os.environ["OCIFS_IAM_TYPE"]
    elif os.environ.get("OCI_IAM_TYPE"):
        os.environ["OCIFS_IAM_TYPE"] = os.environ["OCI_IAM_TYPE"]
    elif os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
        os.environ["OCIFS_IAM_TYPE"] = "resource_principal"
        os.environ["OCI_IAM_TYPE"] = "resource_principal"
    else:
        os.environ["OCIFS_IAM_TYPE"] = "api_key"
        os.environ["OCI_IAM_TYPE"] = "api_key"


setup_default_auth()
