#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import tempfile
from unittest.mock import MagicMock, patch, ANY

import pytest
import os

from ads.model import DataScienceModel
from pandas import DataFrame
from oci_mlflow.deployment import run_local

from oci_mlflow.deployment import OCIModelDeploymentClient


class TestOCIModelDeploymentClient:
    def setup_class(cls):
        cls.curr_dir = os.path.dirname(os.path.abspath(__file__))

    @pytest.fixture()
    def oci_deployment_client(self):
        files_before = set(os.listdir(os.path.join(self.curr_dir, "test_files")))
        yield OCIModelDeploymentClient(target_uri="test://target_uri")
        files_after = set(os.listdir(os.path.join(self.curr_dir, "test_files")))
        generated_files = files_after - files_before
        print(generated_files)
        for file in generated_files:
            os.remove(os.path.join(self.curr_dir, "test_files", file))
        if os.path.exists("my_model_1.0.zip"):
            os.remove("my_model_1.0.zip")

    @patch("oci_mlflow.deployment.MlflowClient")
    @patch("oci_mlflow.deployment.DataScienceModel.create")
    def test_create_model(
        self, mock_create, mocked_mlflow_client, oci_deployment_client
    ):
        mocked_mlflow_client.return_value.tracking_uri = "test_sth"
        mocked_mlflow_client.return_value.get_model_version.return_value.run_id = (
            "test_run_id"
        )
        mocked_mlflow_client.return_value.get_model_version.return_value.source = (
            "test_source"
        )
        mocked_mlflow_client.return_value.get_model_version.return_value.source = (
            "test_source"
        )
        mocked_mlflow_client.return_value.get_model_version.return_value.compartment_id = (
            "testCompartment"
        )
        mocked_mlflow_client.return_value.get_model_version.return_value.project_id = (
            "testProject"
        )
        mock_create.return_value = MagicMock()

        model_uri = "oci://bucket/model"
        infra_spec = {"spec": {"type": "example"}}
        name = "my_model"
        version = "1.0"
        model_local_dir = os.path.join(self.curr_dir, "test_files")
        conda_uri = "oci://bucket/conda_pack.tar.gz"
        python_version = "3.8"
        score_code = None

        model = oci_deployment_client.create_model(
            model_uri,
            infra_spec,
            name,
            version,
            model_local_dir,
            conda_uri,
            python_version,
            score_code,
        )

        assert model is not None

    @patch("oci_mlflow.deployment.MlflowClient")
    def test_create_model_value_error(
        self, mocked_mlflow_client, oci_deployment_client
    ):
        mocked_mlflow_client.return_value.tracking_uri = "test_sth"
        mocked_mlflow_client.return_value.get_model_version.return_value.run_id = (
            "test_run_id"
        )
        mocked_mlflow_client.return_value.get_model_version.return_value.source = (
            "test_source"
        )
        mocked_mlflow_client.return_value.get_model_version.return_value.source = (
            "test_source"
        )
        mocked_mlflow_client.return_value.get_model_version.return_value.compartment_id = (
            "testCompartment"
        )
        mocked_mlflow_client.return_value.get_model_version.return_value.project_id = (
            "testProject"
        )

        model_uri = "test://bucket/model"
        infra_spec = {"spec": {"type": "example"}}
        name = "my_model"
        version = "1.0"
        model_local_dir = os.path.join(self.curr_dir, "test_files")
        conda_uri = "test://bucket/conda_pack.tar.gz"
        python_version = "3.8"
        score_code = "error.py"

        with pytest.raises(ValueError):
            oci_deployment_client.create_model(
                model_uri,
                infra_spec,
                name,
                version,
                model_local_dir,
                conda_uri,
                python_version,
                score_code,
            )

    def test_create_conda_environment(self, oci_deployment_client):
        name = "test_model"
        runtime = {
            "spec": {
                "uri": "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh",
                "pythonVersion": "3.9",
            }
        }
        model_local_dir = tempfile.TemporaryDirectory()
        conda_info = oci_deployment_client.create_conda_environment(
            name, runtime, model_local_dir.name
        )
        assert (
            conda_info.uri
            == "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
        )
        assert conda_info.python_version == "3.9"
        assert conda_info.keep_local is None
        assert conda_info.slug is None

    def test_create_conda_environment_missing_uri(self, oci_deployment_client):
        name = "test_model"
        runtime = {"spec": {"pythonVersion": "3.9"}}
        model_local_dir = tempfile.TemporaryDirectory()
        with pytest.raises(
            Exception, match="Missing URI attribute under conda runtime"
        ):
            oci_deployment_client.create_conda_environment(
                name, runtime, model_local_dir.name
            )

    def test_create_conda_environment_missing_python_version(
        self, oci_deployment_client
    ):
        name = "test_model"
        runtime = {
            "spec": {
                "uri": "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
            }
        }
        model_local_dir = tempfile.TemporaryDirectory()
        with pytest.raises(
            ValueError,
            match="Could not determine the python version of the provided conda environment",
        ):
            oci_deployment_client.create_conda_environment(
                name, runtime, model_local_dir.name
            )

    def test_create_conda_environment_str_uri_type(self, oci_deployment_client):
        name = "test_model"
        runtime = {"spec": {"uri": "sthRandom", "pythonVersion": "3.9"}}
        model_local_dir = tempfile.TemporaryDirectory()

        result = oci_deployment_client.create_conda_environment(
            name, runtime, model_local_dir.name
        )
        assert result is not None

    @patch("oci_mlflow.deployment.build_and_publish_conda_pack")
    def test_create_conda_environment_dict_uri_type(
        self, mock_build, oci_deployment_client
    ):
        name = "test_model"
        runtime = {
            "spec": {
                "uri": {
                    "localCondaDir": "/path/to/local/conda/dir",
                    "version": "2",
                    "gpu": True,
                    "overwrite": True,
                    "destination": "/path/to/conda/pack/destination",
                },
                "pythonVersion": "3.9",
            }
        }
        model_local_dir = os.path.join(self.curr_dir, "test_files")

        result = oci_deployment_client.create_conda_environment(
            name, runtime, model_local_dir
        )
        assert result is not None

    @patch("oci_mlflow.deployment.MlflowClient")
    @patch("oci_mlflow.deployment.download_artifacts")
    def test_fetch_model_artifact(
        self, mock_download_artifacts, mock_mlflow_client, oci_deployment_client
    ):
        model_uri = "models:/test_model/1"
        mock_download_artifacts.return_value = None
        mock_mlflow_client.return_value.get_model_version_download_uri.return_value = (
            "oci://my-bucket/path/to/artifact"
        )

        name, version, dst_path = oci_deployment_client.fetch_model_artifact(model_uri)
        assert name == "test_model"
        assert version == "1"
        assert dst_path is not None

    def test_create_deployment_invalid_flavor(self, oci_deployment_client):
        with pytest.raises(NotImplementedError):
            oci_deployment_client.create_deployment(
                name="test-deployment",
                model_uri="test-model-uri",
                flavor="invalid_flavor",
            )

    def test_create_deployment_invalid_config_file(self, oci_deployment_client):
        with pytest.raises(Exception):
            oci_deployment_client.create_deployment(
                name="test-deployment", model_uri="test-model-uri", config={}
            )

    @patch("oci_mlflow.deployment.DataScienceModel.delete")
    @patch("oci_mlflow.deployment.ModelDeployment.__init__")
    @patch("oci_mlflow.deployment.MlflowClient")
    @patch.object(
        OCIModelDeploymentClient,
        "create_model",
        return_value=DataScienceModel(id="test_files/test-model"),
    )
    @patch.object(
        OCIModelDeploymentClient,
        "fetch_model_artifact",
        return_value=("test-model", "1", tempfile.TemporaryDirectory()),
    )
    def test_create_deployment_container_runtime(
        self,
        mock_fetch,
        mock_create_model,
        mock_set_tag,
        mock_model_deploy,
        mock_model_delete,
        oci_deployment_client,
    ):
        mock_model_deploy.return_value = None
        mock_model_delete.return_value = None
        oci_deployment_client.create_deployment(
            name="test-deployment",
            model_uri="test-model-uri",
            flavor="python_function",
            config={
                "deploy-config-file": os.path.join(
                    self.curr_dir,
                    "test_files" "/oci" "-datascience" "-template_test" ".yaml",
                )
            },
        )
        mock_fetch.assert_called_once_with("test-model-uri")
        mock_create_model.assert_called_once_with(
            "test-model-uri", ANY, "test-model", "1", ANY, None, None, score_code=ANY
        )

    @patch("oci_mlflow.deployment.ModelDeployment.from_id")
    def test_update_deployment_success(self, mock_update, oci_deployment_client):
        # Arrange
        mock_update.return_value.model_deployment_id = "testMdId"
        name = "test_deployment"
        config = {
            "deploy-config-file": os.path.join(
                self.curr_dir, "test_files/oci-datascience-template_test.yaml"
            )
        }
        spec = {
            "spec": {
                "infrastructure": {"compute": {"shape": "VM.Standard2.1"}},
                "display_name": "Test Deployment",
            }
        }

        result = oci_deployment_client.update_deployment(
            name, config=config, endpoint=None, flavor=None, model_uri=None
        )

        assert result is not None
        assert result["flavor"] == "python_function"
        assert result["name"] == "testMdId"

    @patch("oci_mlflow.deployment.ModelDeployment.from_id")
    def test_update_deployment_failure(self, mock_update, oci_deployment_client):
        name = "test_deployment"
        config = {}
        with pytest.raises(Exception):
            oci_deployment_client.update_deployment(
                name, config=config, endpoint=None, flavor=None, model_uri=None
            )

    @patch("oci_mlflow.deployment.ModelDeployment.from_id")
    @patch("oci_mlflow.deployment.requests.post")
    def test_predict(self, mock_post, mock_md, oci_deployment_client):
        mock_md.return_value.url = "https://test.com"
        inputs = {"input": [1, 2, 3]}
        mock_post.return_value = {"result": [4, 5, 6]}

        result = oci_deployment_client.predict(deployment_name="test", inputs=inputs)

        assert result is not None
        assert isinstance(result, DataFrame)

    @patch("oci_mlflow.deployment.ModelDeployment")
    def test_delete_deployment(self, mock_model_deployment, oci_deployment_client):
        name = "test_deployment"
        oci_deployment_client.delete_deployment(name)
        mock_model_deployment.from_id.assert_called_once_with(name)
        mock_model_deployment.from_id.return_value.delete.assert_called_once()

    @patch("oci_mlflow.deployment.ModelDeployment")
    def test_get_deployment(self, mock_model_deployment, oci_deployment_client):
        name = "test_deployment"
        mock_model = MagicMock()
        mock_model_deployment.from_id.return_value = mock_model
        response = oci_deployment_client.get_deployment(name)
        mock_model_deployment.from_id.assert_called_once_with(name)
        assert response == {"model": mock_model}

    def test_list_deployments(self, oci_deployment_client):
        with pytest.raises(NotImplementedError):
            oci_deployment_client.list_deployments()

    def test_run_local(self, oci_deployment_client):
        with pytest.raises(NotImplementedError):
            run_local()
