#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import inspect
import os
from dataclasses import dataclass
from typing import Dict, Union

import ads
import ocifs
import yaml
from ads.common.auth import AuthType, default_signer
from ads.opctl.conda.cmds import _create, _publish
from ads.opctl.config.base import ConfigProcessor
from ads.opctl.config.merger import ConfigMerger
from ads.opctl.constants import DEFAULT_ADS_CONFIG_FOLDER
from oci.config import DEFAULT_LOCATION, DEFAULT_PROFILE

from oci_mlflow import __version__, logger

OCIFS_IAM_TYPE = "OCIFS_IAM_TYPE"
WORK_DIR = "{work_dir}"

DEFAULT_TAGS = {"oracle_ads": ads.__version__, "oci_mlflow": __version__}


class UnsupportedAuthTypeError(Exception):
    def __init__(self, auth_type: str):
        super().__init__(
            f"The provided authentication type: {auth_type} is not supported. "
            f"Allowed values are: {AuthType.values()}"
        )


@dataclass
class OCIBackendConfig:
    """Class representing OCI config.

    Attributes
    ----------
    oci_auth: str
        OCI auth type.
    oci_config_path: str
        Path to the OCI auth config.
    oci_profile: str
        The OCI auth profile.
    """

    oci_auth: str = ""
    oci_config_path: str = ""
    oci_profile: str = ""

    def __post_init__(self):
        self._validate()

    def _validate(self):

        # authentication type
        self.oci_auth = (
            self.oci_auth
            or os.environ.get(OCIFS_IAM_TYPE)
            or AuthType.RESOURCE_PRINCIPAL
        )
        if self.oci_auth not in AuthType:
            raise UnsupportedAuthTypeError(self.oci_auth)

        # OCI AUTH config path
        self.oci_config_path = self.oci_config_path or DEFAULT_LOCATION

        # OCI AUTH profile
        self.oci_profile = self.oci_profile or DEFAULT_PROFILE

    @classmethod
    def from_dict(cls, config: Dict[str, str]) -> "OCIBackendConfig":
        """Creates an instance of the OCIBackendConfig class from a dictionary.

        Parameters
        ----------
        config: Dict[str, str]
            List of properties and values in dictionary format.

        Returns
        -------
        OCIBackendConfig
            Instance of the OCIBackendConfig.
        """
        if not config:
            return cls()

        return cls(
            **{
                k: v
                for k, v in config.items()
                if k in inspect.signature(cls).parameters
            }
        )


@dataclass
class OCIProjectBackendConfig(OCIBackendConfig):
    """Class representing OCI project backend config.

    Attributes
    ----------
    oci_job_template_path: str
        Path to the Job template YAML.
    project_uri: str
        The project content location.
    work_dir: str
        The project work dir.
    """

    oci_job_template_path: str = ""
    project_uri: str = ""
    work_dir: str = ""

    def __post_init__(self):
        super()._validate()
        self._validate()

    def _validate(self):

        # project URI
        if not self.project_uri:
            raise ValueError("The `project_uri` is not provided.")

        # work dir
        if not self.work_dir:
            raise ValueError("The `work_dir` is not provided.")
        self.work_dir = os.path.abspath(os.path.expanduser(self.work_dir))

        # Job template path
        if not self.oci_job_template_path:
            raise ValueError(
                "The `oci_job_template_path` is not provided in `oci-config.json`."
            )
        self.oci_job_template_path = os.path.abspath(
            os.path.expanduser(
                self.oci_job_template_path.replace(WORK_DIR, self.work_dir)
            )
        )

        if not os.path.exists(self.oci_job_template_path):
            raise ValueError(f"The `{self.oci_job_template_path}` does not exist.")

        if not self.oci_job_template_path.lower().endswith((".yml", ".yaml")):
            raise ValueError(
                f"Unsupported file format for the `{self.oci_job_template_path}`. "
                "Allowed formats are: [.yaml, .yml]"
            )


def generate_slug(name: str, version: str) -> str:
    return f"{name}_v{version}".replace(" ", "").replace(".", "_").lower()


def generate_conda_pack_uri(
    name: str, version: str, conda_pack_os_prefix: str, slug: str, gpu: bool
) -> str:
    return os.path.join(
        conda_pack_os_prefix,
        "gpu" if gpu else "cpu",
        name,
        version,
        slug,
    )


def create_conda(
    name: str,
    version: str = "1",
    environment_file: str = None,
    conda_pack_folder: str = None,
    gpu: bool = False,
    overwrite: bool = False,
) -> str:
    """
    Creates conda pack and returns slug name
    """
    logger.info("Creating conda environment with details - ")
    with open(environment_file) as ef:
        logger.info(ef.read())
    return _create(name, version, environment_file, conda_pack_folder, gpu, overwrite)


# TODO: Move conda create and publish to ADS - https://jira.oci.oraclecorp.com/browse/ODSC-38641
def publish(
    slug: str,
    conda_pack_os_prefix: str,
    conda_pack_folder: str,
    overwrite: bool,
    ads_config: str = DEFAULT_ADS_CONFIG_FOLDER,
    name: str = " ",
    version: str = "1",
    gpu: bool = False,
):
    """
    Publishes the conda pack to object storage

    TODO: Remove name and version parameter once ADS publish method is updated to return conda pack URI
    """
    logger.info(
        f"Publishing conda environment to object storage: {conda_pack_os_prefix}"
    )
    p = ConfigProcessor().step(ConfigMerger, ads_config=ads_config)
    exec_config = p.config["execution"]
    # By default the publish uses container to zip and upload the artifact.
    # Setting the environment variable to use host to upload the artifact.
    publish_option = os.environ.get("NO_CONTAINER")
    os.environ["NO_CONTAINER"] = "True"
    _publish(
        conda_slug=slug,
        conda_uri_prefix=conda_pack_os_prefix,
        conda_pack_folder=conda_pack_folder,
        overwrite=overwrite,
        oci_config=exec_config.get("oci_config"),
        oci_profile=exec_config.get("oci_profile"),
        auth_type=exec_config["auth"],
    )
    if publish_option:
        os.environ["NO_CONTAINER"] = publish_option
    else:
        os.environ.pop("NO_CONTAINER", None)

    return generate_conda_pack_uri(name, version, conda_pack_os_prefix, slug, gpu)


def build_and_publish_conda_pack(
    name: str,
    version: str,
    environment_file: str,
    conda_pack_folder: str,
    conda_pack_os_prefix: str,
    gpu: bool = False,
    overwrite: bool = False,
    ads_config: str = DEFAULT_ADS_CONFIG_FOLDER,
):
    """
    * If overwrite then create and publish always
    * If not overwrite and conda_os_uri exists, skip create and publish. let user know
    * If not overwrite and conda_os_uri does not exsits, but local conda pack exists, found local environment, publishing from local copy

    """
    slug = generate_slug(name, version)
    conda_pack_uri = generate_conda_pack_uri(
        name=name,
        version=version,
        conda_pack_os_prefix=conda_pack_os_prefix,
        slug=slug,
        gpu=gpu,
    )
    fs = ocifs.OCIFileSystem(**default_signer())
    if fs.exists(conda_pack_uri) and not overwrite:
        logger.info(
            f"Conda pack exists at {conda_pack_uri}. Skipping build and publish. If you want to overwrite, set overwrite to true"
        )
    else:
        if os.path.exists(os.path.join(conda_pack_folder, slug)) and not overwrite:
            logger.info(
                f"Found an environment at {os.path.join(conda_pack_folder, slug)} which matches the name and version. Change version to create a new pack or set overwrite to true"
            )
        else:
            create_conda(
                name, version, environment_file, conda_pack_folder, gpu, overwrite
            )
            logger.info(
                f"Created conda pack at {os.path.join(conda_pack_folder, slug)}"
            )
        conda_pack_uri = publish(
            slug,
            conda_pack_os_prefix=conda_pack_os_prefix,
            conda_pack_folder=conda_pack_folder,
            overwrite=overwrite,
            ads_config=ads_config,
            gpu=gpu,
            name=name,
            version=version,
        )
        logger.info(f"Published conda pack at {conda_pack_uri}")
    return conda_pack_uri


def resolve_python_version(conda_yaml_file: str) -> Union[str, None]:
    """
    Loops through the dependencies section inside the conda yaml file to search for python version.

    Limitation: Assumes pattern - python=version. Will fail if the yaml has python{><}=version
    """
    version = None
    with open(conda_yaml_file) as cf:
        env = yaml.load(cf, Loader=yaml.SafeLoader)
        python = [
            dep
            for dep in env["dependencies"]
            if isinstance(dep, str) and dep.startswith("python")
        ]
        version = python[0].split("=")[1] if len(python) > 0 else None
    return version
