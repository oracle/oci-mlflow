#!/usr/bin/env python
# coding: utf-8

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/


import io
import json
import os

from setuptools import find_packages, setup

VERSION = "UNKNOWN"


def open_relative(*path):
    """
    Opens files in read-only with a fixed utf-8 encoding.
    All locations are relative to this setup.py file.
    """
    return io.open(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), *path),
        mode="r",
        encoding="utf-8",
    )


with open_relative("oci_mlflow", "version.json") as version_file:
    VERSION = json.load(version_file)["version"]

with open_relative("README.md") as f:
    readme = f.read()

install_requires = [
    "mlflow>=2.3.2",
    "oracle-ads>=2.8.8",
]

extras_require = {"dev": ["pytest", "pytest-cov", "pytest-env"]}
setup(
    name="oci-mlflow",
    version=VERSION,
    description="OCI MLflow plugin to use OCI resources within MLflow",
    author="Oracle Cloud Infrastructure Data Science",
    license="Universal Permissive License 1.0",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires=">=3.8",
    keywords="Oracle Cloud Infrastructure, OCI, Object Storage, MLflow",
    entry_points={
        "mlflow.artifact_repository": "oci=oci_mlflow.oci_object_storage:OCIObjectStorageArtifactRepository",
        "mlflow.project_backend": "oci-datascience=oci_mlflow.project:OCIProjectBackend",
        "mlflow.deployments": "oci-datascience=oci_mlflow.deployment",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Universal Permissive License (UPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
