#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import os
from unittest.mock import patch, ANY

import pytest

from oci_mlflow import utils
from oci_mlflow.utils import (
    OCIBackendConfig,
    OCIProjectBackendConfig,
    UnsupportedAuthTypeError,
    generate_conda_pack_uri,
    generate_slug,
    create_conda,
    resolve_python_version,
    publish,
)


class TestOCIBackendConfig:
    """Tests the OCIBackendConfig."""

    def test_from_dict_with_empty_dict(self):
        config = {}

        result = OCIBackendConfig.from_dict(config)

        assert isinstance(result, OCIBackendConfig)

    def test_from_dict_with_valid_dict(self):
        config = {"oci_auth": "resource_principal", "oci_profile": "testVal2"}

        result = OCIBackendConfig.from_dict(config)
        assert isinstance(result, OCIBackendConfig)
        assert result.oci_auth == "resource_principal"
        assert result.oci_profile == "testVal2"

    def test_from_dict_with_invalid_dict(self):
        config = {"oci_auth": "test_ErrorVal", "oci_profile": "testVal2"}

        with pytest.raises(UnsupportedAuthTypeError):
            OCIProjectBackendConfig.from_dict(config)


class TestOCIProjectBackendConfig:
    """Tests the OCIProjectBackendConfig."""

    def setup_class(cls):
        cls.curr_dir = os.path.dirname(os.path.abspath(__file__))

    def test_post_init_with_valid_values(self):
        config = {
            "oci_auth": "resource_principal",
            "oci_profile": "testVal2",
            "oci_job_template_path": "{work_dir}/test_files/oci-datascience-template_test.yaml",
            "project_uri": "/path/to/project",
            "work_dir": self.curr_dir,
        }

        project_backend_config = OCIProjectBackendConfig.from_dict(config)

        assert project_backend_config.oci_job_template_path == os.path.join(
            self.curr_dir, "test_files/oci-datascience-template_test.yaml"
        )
        assert project_backend_config.project_uri == "/path/to/project"
        assert project_backend_config.work_dir == self.curr_dir

    def test_post_init_with_missing_project_uri(self):
        config_dict = {
            "oci_auth": "resource_principal",
            "oci_job_template_path": "test_files/oci-datascience-template_test.yaml",
            "work_dir": "/path/to/work_dir",
        }

        with pytest.raises(ValueError):
            OCIProjectBackendConfig.from_dict(config_dict)

    def test_post_init_with_missing_work_dir(self):
        config_dict = {
            "oci_auth": "resource_principal",
            "oci_job_template_path": "test_files/oci-datascience-template_test.yaml",
            "project_uri": "/path/to/project",
        }

        with pytest.raises(ValueError):
            OCIProjectBackendConfig.from_dict(config_dict)

    def test_post_init_with_missing_oci_job_template_path(self):
        config_dict = {
            "oci_auth": "resource_principal",
            "project_uri": "/path/to/project",
            "work_dir": "/path/to/work_dir",
        }

        with pytest.raises(ValueError):
            OCIProjectBackendConfig.from_dict(config_dict)

    def test_post_init_with_invalid_oci_job_template_path(self):
        config_dict = {
            "oci_job_template_path": "test_files/invalid-file-type.html",
            "project_uri": "/path/to/project",
            "work_dir": "/path/to/work_dir",
        }

        with pytest.raises(ValueError):
            OCIProjectBackendConfig.from_dict(config_dict)

    def test_post_init_with_invalid_oci_job_template_extension(self):
        config_dict = {
            "oci_job_template_path": "{work_dir}/test_files/invalid-file-type.txt",
            "project_uri": "/path/to/project",
            "work_dir": self.curr_dir,
        }

        with pytest.raises(ValueError):
            OCIProjectBackendConfig.from_dict(config_dict)


class TestUtils:
    """Tests the common methods in the utils module."""

    def setup_class(cls):
        cls.curr_dir = os.path.dirname(os.path.abspath(__file__))

    def test_generate_slug(self):
        assert generate_slug("Test Sth", "1.0.1") == "teststh_v1_0_1"

    def test_generate_conda_pack_uri(self):
        assert generate_conda_pack_uri(
            "test_package", "1.0", "/path/to/prefix", "test_package_v1", False
        ) == os.path.join(
            "/path/to/prefix", "cpu", "test_package", "1.0", "test_package_v1"
        )

        assert generate_conda_pack_uri(
            "test_package", "1.0", "/path/to/prefix", "test_package_v1_0", True
        ) == os.path.join(
            "/path/to/prefix", "gpu", "test_package", "1.0", "test_package_v1_0"
        )

    @patch("oci_mlflow.utils._create")
    def test_create_conda(self, mock_create):
        mock_create.return_value = "test_return_val"
        assert create_conda(
            "dummy_name",
            "1",
            os.path.join(
                self.curr_dir, "test_files/oci-datascience-template_test" ".yaml"
            )
            == "test_return_val",
        )

    def test_resolve_python_version(self):
        assert (
            resolve_python_version(
                os.path.join(
                    self.curr_dir, "test_files/oci-datascience-template_test.yaml"
                )
            )
            == "3.8"
        )

    @patch("oci_mlflow.utils.ConfigProcessor")
    @patch.object(utils, "generate_conda_pack_uri")
    @patch("oci_mlflow.utils._publish")
    def test_publish(self, mock_publish, mock_generate_conda_pack, mock_config):
        slug = "test_slug"
        conda_pack_os_prefix = "test_prefix"
        conda_pack_folder = "test_folder"
        overwrite = False
        ads_config = "test_config"
        name = "test_name"
        version = "test_version"
        gpu = False

        publish(
            slug,
            conda_pack_os_prefix,
            conda_pack_folder,
            overwrite,
            ads_config,
            name,
            version,
            gpu,
        )

        mock_config.assert_called_once()
        mock_generate_conda_pack.assert_called_once_with(
            name, version, conda_pack_os_prefix, slug, gpu
        )
        mock_publish.assert_called_once_with(
            conda_slug=slug,
            conda_uri_prefix=conda_pack_os_prefix,
            conda_pack_folder=conda_pack_folder,
            overwrite=overwrite,
            oci_config=ANY,
            oci_profile=ANY,
            auth_type=ANY,
        )
