#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import os
from dataclasses import asdict
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

import pytest
from ads.jobs import NotebookRuntime
from ads.jobs.builders.infrastructure.dataflow import DataFlowApp
from ads.jobs.builders.infrastructure.dsc_job import DSCJob
from mlflow.exceptions import ExecutionException

from oci_mlflow.project import (
    GitPythonRuntimeDecorator,
    ContainerRuntimeDecorator,
    ScriptRuntimeDecorator,
    PythonRuntimeDecorator,
)

from oci_mlflow.project import (
    EntryPointCommand,
    JobRuntimeDecoratorFactory,
    MLflowTagsLogger,
    NotebookRuntimeDecorator,
    OCIProjectBackend,
    OCIProjectRun,
    RunnableInstanceDecorator,
    RuntimeDecorator,
    UnsupportedJobRuntime,
)


class TestEntryPointCommand:
    def test_from_project_cmd_empty_string(self):
        cmd = ""
        expected = {"cmd": "", "entry_point": "", "args": []}
        actual = asdict(EntryPointCommand.from_project_cmd(cmd))
        assert actual == expected

    def test_from_project_cmd_basic_command(self):
        cmd = "python test.py --testArg testVal"
        expected = {
            "cmd": "python test.py --testArg testVal",
            "entry_point": "test.py",
            "args": ["--testArg", "testVal"],
        }
        actual = asdict(EntryPointCommand.from_project_cmd(cmd))
        assert actual == expected

    def test_from_project_cmd_multiple_arguments(self):
        cmd = "python test.py --param1 value1 --param2 value2"
        expected = {
            "cmd": "python test.py --param1 value1 --param2 value2",
            "entry_point": "test.py",
            "args": ["--param1", "value1", "--param2", "value2"],
        }
        actual = asdict(EntryPointCommand.from_project_cmd(cmd))
        assert actual == expected


class TestOCIProjectRun:
    def test_init(self):
        mlflow_run_id = "mlflow-run-id"
        job_run = Mock()
        run = OCIProjectRun(mlflow_run_id, job_run)
        assert run.mlflow_run_id == mlflow_run_id
        assert run.job_run == job_run

    def test_wait_failed(self):
        job_run = Mock()
        job_run.status = "FAILED"
        run = OCIProjectRun("mlflow-run-id", job_run)
        with pytest.raises(ExecutionException):
            run.wait()

    def test_get_status(self):
        job_run = Mock()
        job_run.status = "SUCCEEDED"
        run = OCIProjectRun("mlflow-run-id", job_run)
        assert run.get_status() == 3

    def test_cancel(self):
        job_run = Mock()
        run = OCIProjectRun("mlflow-run-id", job_run)
        run.cancel()
        job_run.cancel.assert_called_once()

    def test_run_id(self):
        mlflow_run_id = "mlflow-run-id"
        job_run = Mock()
        run = OCIProjectRun(mlflow_run_id, job_run)
        assert run.run_id == mlflow_run_id


class TestOCIProjectBackend:
    @pytest.fixture
    def oci_backend(self):
        return OCIProjectBackend()

    def setup_class(cls):
        cls.curr_dir = os.path.dirname(os.path.abspath(__file__))

    @patch("oci_mlflow.project.get_or_create_run")
    @patch("oci_mlflow.project.fetch_and_validate_project")
    @patch("oci_mlflow.project.load_project")
    @patch("oci_mlflow.project.get_run_env_vars")
    @patch.object(EntryPointCommand, "from_project_cmd")
    @patch("oci_mlflow.project.Job")
    @patch.object(MLflowTagsLogger, "__init__")
    @patch.object(MLflowTagsLogger, "log")
    def test_run(
        self,
        mock_log,
        mock_logger,
        mock_job,
        mock_from_project_cmd,
        mock_get_run_env_vars,
        mock_load_project,
        mock_fetch_and_validate_project,
        mock_get_or_create_run,
        oci_backend,
    ):
        project_uri = "https://github.com/mlflow/mlflow-example"
        entry_point = "train.py"
        params = {"alpha": 0.5}
        version = "master"
        backend_config = {
            "oci_auth": "resource_principal",
            "oci_profile": "testVal2",
            "oci_job_template_path": "{work_dir}/test_files/oci-datascience-template_test.yaml",
            "project_uri": "/path/to/project",
            "work_dir": self.curr_dir,
        }
        tracking_uri = "http://localhost:5000"
        experiment_id = "1"

        mock_fetch_and_validate_project.return_value = self.curr_dir
        mock_get_run_env_vars.return_value = None
        mock_from_project_cmd.return_value = None
        mock_logger.return_value = None
        mock_job.return_value = None

        run = oci_backend.run(
            project_uri,
            entry_point,
            params,
            version,
            backend_config,
            tracking_uri,
            experiment_id,
        )

        mock_load_project.assert_called_once_with(self.curr_dir)
        assert run is not None

    def test_run_with_invalid_project_uri(self, oci_backend):
        with pytest.raises(ExecutionException):
            oci_backend.run(
                "test_invalid_uri",
                "main",
                {"arg1": "value1"},
                "version",
                {},
                "http://localhost:5000",
                "123",
            )


class TestJobRuntimeDecoratorFactory:
    def test_get_decorator(self):
        assert isinstance(
            JobRuntimeDecoratorFactory.get_decorator(
                NotebookRuntime().type,
                work_dir="/path/to/work_dir",
                active_run=None,
                project=None,
                runtime=None,
                entry_point_command=None,
                env_vars=None,
                oci_backend_config=None,
                tmp_dir="/path/to/tmp_dir",
                version=1,
            ),
            NotebookRuntimeDecorator,
        )

        with pytest.raises(UnsupportedJobRuntime):
            JobRuntimeDecoratorFactory.get_decorator("unsupported_runtime_type")


class TestRunTimeDecorator:
    def test_runtime_decorator(self):
        work_dir = "/path/to/project"
        active_run = mock.MagicMock()
        active_run.info.run_uuid = "test-run-uuid"
        active_run.info.experiment_id = "test-experiment-id"
        active_run.info.run_name = "test-run-name"
        project = mock.MagicMock()
        runtime = mock.MagicMock()
        entry_point_command = mock.MagicMock()
        env_vars = {"VAR1": "value1", "VAR2": "value2"}
        oci_backend_config = mock.MagicMock()
        tmp_dir = "/path/to/tmp"
        version = "main"

        runtime_decorator = RuntimeDecorator(
            work_dir,
            active_run,
            project,
            runtime,
            entry_point_command,
            env_vars,
            oci_backend_config,
            tmp_dir,
            version,
        )

        # Test that the attributes are correctly set
        assert runtime_decorator.work_dir == work_dir
        assert runtime_decorator.active_run == active_run
        assert runtime_decorator.project == project
        assert runtime_decorator.runtime == runtime
        assert runtime_decorator.entry_point_command == entry_point_command
        assert runtime_decorator.env_vars == env_vars


class TestRunnableInstanceDecorator:
    def test_runnable_instance_decorator(self):
        work_dir = "/path/to/project"
        active_run = mock.MagicMock()
        active_run.info.run_uuid = "test-run-uuid"
        active_run.info.experiment_id = "test-experiment-id"
        active_run.info.run_name = "test-run-name"
        project = mock.MagicMock()
        runtime = mock.MagicMock()
        entry_point_command = mock.MagicMock()
        env_vars = {"VAR1": "value1", "VAR2": "value2"}
        oci_backend_config = mock.MagicMock()
        tmp_dir = "/path/to/tmp"
        version = "main"

        runtime_decorator = RunnableInstanceDecorator(
            work_dir,
            active_run,
            project,
            runtime,
            entry_point_command,
            env_vars,
            oci_backend_config,
            tmp_dir,
            version,
        )

        assert runtime_decorator.work_dir == work_dir
        assert runtime_decorator.active_run == active_run
        assert runtime_decorator.project == project
        assert runtime_decorator.entry_point_command == entry_point_command


class TestMLflowTagsLogger:
    @pytest.fixture
    def logger(self):
        job = MagicMock()
        job_run = MagicMock()
        project = MagicMock()
        active_run = MagicMock()
        client = MagicMock()

        with patch.object(DataFlowApp, "__init__", return_value=None):
            with patch.object(DSCJob, "__init__", return_value=None):
                mlflowLogger = MLflowTagsLogger(
                    job, job_run, project, active_run, client
                )

        return mlflowLogger

    def test_log_default_tags(self, logger):
        logger.log()
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id, "job_id", logger.job.id
        )
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id, "job_run_id", logger.job_run.id
        )
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id,
            "job_run_link",
            logger.job_run.run_details_link,
        )

    def test_log_data_science_job_tags(self, logger):
        logger.job.infrastructure.type = "dataScienceJob"
        logger.log()
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id, "shape", logger.job.infrastructure.shape_name
        )
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id,
            "shape_memory_gbs",
            logger.job.infrastructure.shape_config_details.get("memoryInGBs"),
        )
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id,
            "shape_ocpus",
            logger.job.infrastructure.shape_config_details.get("ocpus"),
        )

    def test_log_data_flow_job_tags(self, logger):
        logger.job.infrastructure.type = "dataFlow"
        logger.log()
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id,
            "driver_shape",
            logger.job.infrastructure.driver_shape,
        )
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id,
            "executor-shape",
            logger.job.infrastructure.executor_shape,
        )
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id,
            "driver_memory_gbs",
            logger.job.infrastructure.driver_shape_config.get("memoryInGBs"),
        )
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id,
            "driver_ocpus",
            logger.job.infrastructure.driver_shape_config.get("ocpus"),
        )
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id,
            "executor_memory_gbs",
            logger.job.infrastructure.executor_shape_config.get("memoryInGBs"),
        )
        logger.client.set_tag.assert_any_call(
            logger.active_run.info.run_id,
            "executor_ocpus",
            logger.job.infrastructure.executor_shape_config.get("ocpus"),
        )

    def test_description_log(self, logger):
        logger._description_log()
        logger.client.set_tag.assert_called()


class TestGitPythonRuntimeDecorator:
    def test_decorate(self):
        work_dir = "/path/to/project"
        active_run = mock.MagicMock()
        active_run.info.run_uuid = "test-run-uuid"
        active_run.info.experiment_id = "test-experiment-id"
        active_run.info.run_name = "test-run-name"
        project = mock.MagicMock()
        runtime = mock.MagicMock()
        entry_point_command = mock.MagicMock()
        env_vars = {"VAR1": "value1", "VAR2": "value2"}
        oci_backend_config = mock.MagicMock()
        tmp_dir = "/path/to/tmp"
        version = "main"

        git_run_time_decorator = GitPythonRuntimeDecorator(
            work_dir,
            active_run,
            project,
            runtime,
            entry_point_command,
            env_vars,
            oci_backend_config,
            tmp_dir,
            version,
        )

        git_run_time_decorator.decorate()
        runtime.with_source.assert_called()


class TestContainerRuntimeDecorator:
    def test_decorate(self):
        work_dir = "/path/to/project"
        active_run = mock.MagicMock()
        active_run.info.run_uuid = "test-run-uuid"
        active_run.info.experiment_id = "test-experiment-id"
        active_run.info.run_name = "test-run-name"
        project = mock.MagicMock()
        runtime = mock.MagicMock()
        entry_point_command = mock.MagicMock()
        env_vars = {"VAR1": "value1", "VAR2": "value2"}
        oci_backend_config = mock.MagicMock()
        tmp_dir = "/path/to/tmp"
        version = "main"
        entry_point_command.cmd = "testCmd"

        container_runtime_decorator = ContainerRuntimeDecorator(
            work_dir,
            active_run,
            project,
            runtime,
            entry_point_command,
            env_vars,
            oci_backend_config,
            tmp_dir,
            version,
        )

        container_runtime_decorator.decorate()
        runtime.with_cmd.assert_called_with("testCmd")


class TestScriptRuntimeDecorator:
    def test_decorate(self):
        work_dir = "/path/to/project"
        active_run = mock.MagicMock()
        active_run.info.run_uuid = "test-run-uuid"
        active_run.info.experiment_id = "test-experiment-id"
        active_run.info.run_name = "test-run-name"
        project = mock.MagicMock()
        runtime = mock.MagicMock()
        entry_point_command = mock.MagicMock()
        env_vars = {"VAR1": "value1", "VAR2": "value2"}
        oci_backend_config = mock.MagicMock()
        tmp_dir = "/path/to/tmp"
        version = "main"

        script_runtime_decorator = ScriptRuntimeDecorator(
            work_dir,
            active_run,
            project,
            runtime,
            entry_point_command,
            env_vars,
            oci_backend_config,
            tmp_dir,
            version,
        )

        script_runtime_decorator.decorate()
        runtime.with_source.assert_called()


class TestPythonRuntimeDecorator:
    def test_decorate(self):
        work_dir = "/path/to/project"
        active_run = mock.MagicMock()
        active_run.info.run_uuid = "test-run-uuid"
        active_run.info.experiment_id = "test-experiment-id"
        active_run.info.run_name = "test-run-name"
        project = mock.MagicMock()
        runtime = mock.MagicMock()
        entry_point_command = mock.MagicMock()
        env_vars = {"VAR1": "value1", "VAR2": "value2"}
        oci_backend_config = mock.MagicMock()
        tmp_dir = "/path/to/tmp"
        version = "main"
        entry_point_command.cmd = "testCmd"

        python_runtime_decorator = PythonRuntimeDecorator(
            work_dir,
            active_run,
            project,
            runtime,
            entry_point_command,
            env_vars,
            oci_backend_config,
            tmp_dir,
            version,
        )

        python_runtime_decorator.decorate()
        runtime.with_source.assert_called()
