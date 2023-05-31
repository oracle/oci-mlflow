#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import json
import os
import re
import shlex
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

import ads
from ads.jobs import (
    ContainerRuntime,
    DataFlow,
    DataFlowNotebookRuntime,
    DataFlowRun,
    DataFlowRuntime,
    DataScienceJob,
    DataScienceJobRun,
    GitPythonRuntime,
    Job,
    NotebookRuntime,
    PythonRuntime,
    ScriptRuntime,
)
from ads.jobs.builders.runtimes.base import Runtime
from jinja2 import Environment, PackageLoader
from mlflow.entities import Experiment, Run, RunStatus
from mlflow.exceptions import ExecutionException
from mlflow.projects._project_spec import Project
from mlflow.projects.backend.abstract_backend import AbstractBackend
from mlflow.projects.submitted_run import SubmittedRun
from mlflow.projects.utils import (
    fetch_and_validate_project,
    get_or_create_run,
    get_run_env_vars,
    load_project,
)
from mlflow.tracking import MlflowClient

from oci_mlflow import logger
from oci_mlflow.utils import (
    DEFAULT_TAGS,
    OCIFS_IAM_TYPE,
    AuthType,
    OCIProjectBackendConfig,
)
from oci_mlflow.telemetry_logging import Telemetry, telemetry

OCIMLflowRunStatusMap = {
    "ACCEPTED": RunStatus.SCHEDULED,
    "IN_PROGRESS": RunStatus.RUNNING,
    "FAILED": RunStatus.FAILED,
    "SUCCEEDED": RunStatus.FINISHED,
    "CANCELING": RunStatus.RUNNING,
    "CANCELED": RunStatus.KILLED,
    "DELETED": RunStatus.KILLED,
    "NEEDS_ATTENTION": RunStatus.FAILED,
}

SUCCESS_STATUS = ["SUCCEEDED", "CANCELED", "DELETED"]


class TemplateFields:
    WORK_DIR = "{work_dir}"


class UnsupportedJobRuntime(Exception):
    def __init__(self, runtime_type: str):
        super().__init__(f"The provided runtime: {runtime_type} is not supported. ")


class UnsupportedRunnableInstance(Exception):
    def __init__(self, service_type: str):
        super().__init__(f"The provided OCI backend: {service_type} is not supported. ")


@dataclass
class EntryPointCommand:
    """The class helper to prepare the entrypoint information for the OCI Job.

    Attributes
    ----------
    cmd: str
        The command that needs to be run.
        Example: `python test.py --param1 value1`
    entry_point: str
        The entry point file for a Job.
        Example: `test.py`
    args: List[str]
        The list of arguments for the entrypoint.
        Example: `["--param1", "value1"]`
    """

    cmd: str = ""
    entry_point: str = ""
    args: List[str] = field(default_factory=list)

    @classmethod
    def from_project_cmd(cls, cmd: str) -> "EntryPointCommand":
        """Builds the entry point object from the string command.

        Parameters
        ----------
        cmd: str
            The command that needs to converted to the entry point command.
            Example: `.from_project_cmd("python test.py --param1 value1")`

        Returns
        -------
        EntryPointCommand
            The instance of the EntryPointCommand.
        """
        obj = cls()
        if not cmd:
            return obj

        obj.cmd = shlex.join(shlex.quote(s) for s in shlex.split(cmd))
        parts = shlex.split(obj.cmd)
        if len(parts) > 0 and parts[0].lower().startswith(
            ("python", "nbconvert", "shell", "bash")
        ):
            parts = parts[1:]
        if len(parts) > 0 and re.match("\-\w+", parts[0]):
            parts = parts[1:]
        if len(parts) > 0:
            obj.entry_point = parts[0]
        if len(parts) > 1:
            for arg in parts[1:]:
                try:
                    obj.args.append(json.loads(arg))
                except:
                    obj.args.append(arg)
        return obj


class OCIProjectRun(SubmittedRun):
    """
    Instance of SubmittedRun corresponding to a OCI Job, launched through
    OCI cervices to run an MLflow project.

    Attributes
    ----------
    run_id: str
        The MLflow run id.
    job_run: Union[DataScienceJobRun, DataFlowRun]
        The DataScience/DataFlow Job Run.
    """

    def __init__(
        self, mlflow_run_id: str, job_run: Union[DataScienceJobRun, DataFlowRun]
    ):
        """Initializes OCIProjectRun instance.

        Parameters
        ----------
        mlflow_run_id: str
            The MLflow run id.
        job_run: DataScienceJobRun
            The DataScience/DataFlow Job Run.
        """
        self.mlflow_run_id = mlflow_run_id
        self.job_run = job_run

    def wait(self) -> bool:
        """
        Waits for the OCI Job run to finish.
        Returning `True` if the run succeeded and `False` otherwise.
        """
        # Wait till the job finished
        try:
            self.job_run.watch()
            if self.job_run.status.upper() in SUCCESS_STATUS:
                return True

            raise ExecutionException(
                f"The OCI Job Run: {self.job_run.id} finished with a status: {self.job_run.status}. "
                "Check the OCI logs to get more details."
            )

        except Exception as ex:
            logger.error(ex)
            raise ExecutionException(
                f"Unexpected error occurred during executing the OCI Job Run: {self.job_run.id}. "
                f"Details: {str(ex)}"
            )

    def get_status(self) -> int:
        """Returns a status of the OCI JobRun."""
        return OCIMLflowRunStatusMap[self.job_run.status]

    def cancel(self) -> None:
        """Cancels the run OCI Job Run."""
        self.job_run.cancel()

    @property
    def run_id(self) -> str:
        """Returns the MLflow Run Id."""
        return self.mlflow_run_id


class OCIProjectBackend(AbstractBackend):
    """Implements an AbstractBackend running the MLflow project on the OCI Jobs/Dataflow service."""

    def __init__(self):
        super().__init__()

    @telemetry("plugin=project&action=run")
    def run(
        self,
        project_uri: str,
        entry_point: str,
        params: Dict,
        version: str,
        backend_config: Dict,
        tracking_uri: str,
        experiment_id: str,
        **kwargs,
    ):
        """
        Runs a project on the OCI infrastructure.

        Parameters
        ----------
        project_uri: str
            URI of the project to execute, e.g. a local filesystem path
               or a Git repository URI like https://github.com/mlflow/mlflow-example
        entry_point: str
            Entry point to run within the project.
        params: Dict
            Dict of parameters to pass to the entry point.
        version: str
            For git-based projects, either a commit hash or a branch name.
        backend_config: Dict
            A dictionary with backend configuration.
        tracking_uri: str
            URI of tracking server against which to log run information related to project execution.
        experiment_id: str
            ID of experiment under which to launch the run.

        Returns
        -------
        OCIProjectRun
            Instance of SubmittedRun corresponding to a OCI Job, launched through OCI cervices ]
            to run an MLflow project.
        """

        telemetry: Telemetry = kwargs.pop("telemetry", None)
        logger.info("Run MLfLow project within OCI backend.")
        logger.debug(f"locals(): {locals()}")

        # fetch and validate project
        # in case of the GIT runtime, the temporary folder will be created where the
        # project will be pulled.
        work_dir = fetch_and_validate_project(
            uri=project_uri,
            version=version,
            entry_point=entry_point,
            parameters=params,
        )
        logger.info(f"work_dir: {work_dir}")

        # create MLflow run
        active_run = get_or_create_run(
            run_id=None,
            uri=project_uri,
            experiment_id=experiment_id,
            work_dir=work_dir,
            version=version,
            entry_point=entry_point,
            parameters=params,
        )

        # load MLflow project
        project = load_project(work_dir)

        # extract environment variables
        env_vars = get_run_env_vars(
            run_id=active_run.info.run_uuid, experiment_id=experiment_id
        )

        # extract entrypoint command
        entry_point_command = EntryPointCommand.from_project_cmd(
            project.get_entry_point(entry_point).compute_command(
                user_parameters=params, storage_dir=None
            )
        )
        logger.info(f"entry_point_command: {entry_point_command}")

        oci_backend_config = OCIProjectBackendConfig.from_dict(
            {
                **backend_config,
                **{"project_uri": project_uri, "work_dir": work_dir},
            }
        )
        logger.info(f"oci_backend_config: {oci_backend_config}")

        # setup authentication to create DataScience/DataFlow job
        ads.set_auth(
            auth=oci_backend_config.oci_auth,
            oci_config_location=oci_backend_config.oci_config_path,
            profile=oci_backend_config.oci_profile,
        )

        # the temporary directory is create on case if some file manipulations will be required
        with tempfile.TemporaryDirectory() as tmp_dir:
            # construct job from YAML
            job = Job.from_yaml(uri=oci_backend_config.oci_job_template_path)

            # decorate job with the parameters provided within MLflow project
            try:
                RunnableInstanceDecoratorFactory.get_decorator(
                    job.kind,
                    work_dir=work_dir,
                    active_run=active_run,
                    project=project,
                    job=job,
                    entry_point_command=entry_point_command,
                    env_vars=env_vars,
                    oci_backend_config=oci_backend_config,
                    tmp_dir=tmp_dir,
                    version=version,
                ).decorate()
            except UnsupportedRunnableInstance as ex:
                logger.warn(
                    f"{str(ex)} "
                    "The project will be executed with the parameters "
                    "provided in the OCI template YAML."
                )

            if telemetry:
                telemetry.add(f"infrastructure={job.infrastructure.type}").add(
                    f"runtime={job.runtime.type}"
                )

            # create a job
            job = job.create()

            logger.info(f"{'*' * 50}Job{'*' * 50}")
            logger.info(job)

            # run the job
            job_run = job.run()
            logger.info(f"{'*' * 50}JobRun{'*' * 50}")
            logger.info(job_run)

            opctl_msg_header = (
                f"{'*' * 40} Run the command below to watch the job progress {'*' * 40}"
            )
            logger.info(opctl_msg_header)
            logger.info(f"ads opctl watch {job_run.id}")
            logger.info("*" * len(opctl_msg_header))

        # add infrastructure related tags to the experiment
        MLflowTagsLogger(
            job=job,
            job_run=job_run,
            project=project,
            active_run=active_run,
            client=MlflowClient(),
        ).log()

        # return an instance of the OCIProjectRun
        return OCIProjectRun(
            mlflow_run_id=active_run.info.run_uuid,
            job_run=job_run,
        )


class MLflowTagsLogger:
    """Class helps to prepare and save tags for the MLflow run and OCI DataScience/Dataflow run."""

    def __init__(
        self,
        job: Job,
        job_run: Union[DataScienceJobRun, DataFlowRun],
        project: Project,
        active_run: Run,
        client: MlflowClient,
    ):

        # registering supported infrastructures
        self._INFRA_LOGGER_MAP = {
            DataScienceJob().type: self._dataScience_job_log,
            DataFlow().type: self._dataflow_job_log,
        }

        self.client = client
        self.job = job
        self.job_run = job_run
        self.active_run = active_run
        self.project = project

    def log(self) -> None:
        """Logs the tags for the provided infrastructure."""

        # log common tags
        for tag_key, tag_value in DEFAULT_TAGS.items():
            self.client.set_tag(self.active_run.info.run_id, tag_key, tag_value)
        if hasattr(self.job, "id"):
            self.client.set_tag(self.active_run.info.run_id, "job_id", self.job.id)
        if hasattr(self.job_run, "id"):
            self.client.set_tag(
                self.active_run.info.run_id, "job_run_id", self.job_run.id
            )
        if hasattr(self.job_run, "run_details_link"):
            self.client.set_tag(
                self.active_run.info.run_id,
                "job_run_link",
                self.job_run.run_details_link,
            )

        # log infra specific tags
        self._INFRA_LOGGER_MAP.get(self.job.infrastructure.type, lambda: None)()

        # populates description field
        self._description_log()

    def _description_log(self):
        """Populates the project description field."""
        _env = Environment(loader=PackageLoader("oci_mlflow", "templates"))
        project_description_template = _env.get_template("project_description.jinja2")
        project_description = project_description_template.render(
            job_info=self.job.to_dict(),
            job_run_info=self.job_run.to_dict(),
            project_name=self.project.name,
        )

        self.client.set_tag(
            self.active_run.info.run_id, "mlflow.note.content", project_description
        )

    def _dataScience_job_log(self):
        """Logs the tags for the DataScience job."""
        self.client.set_tag(
            self.active_run.info.run_id,
            "shape",
            self.job.infrastructure.shape_name,
        )

        self.client.set_tag(
            self.active_run.info.run_id,
            "shape_memory_gbs",
            (self.job.infrastructure.shape_config_details or {}).get("memoryInGBs")
            or (self.job.infrastructure.shape_config_details or {}).get(
                "memory_in_gbs"
            ),
        )
        self.client.set_tag(
            self.active_run.info.run_id,
            "shape_ocpus",
            (self.job.infrastructure.shape_config_details or {}).get("ocpus"),
        )

    def _dataflow_job_log(self):
        """Logs the tags for the DataFlow job."""
        self.client.set_tag(
            self.active_run.info.run_id,
            "driver_shape",
            self.job.infrastructure.driver_shape,
        )
        self.client.set_tag(
            self.active_run.info.run_id,
            "executor-shape",
            self.job.infrastructure.executor_shape,
        )
        if hasattr(self.job.infrastructure, "driver_shape_config"):
            self.client.set_tag(
                self.active_run.info.run_id,
                "driver_memory_gbs",
                (self.job.infrastructure.driver_shape_config or {}).get("memoryInGBs")
                or (self.job.infrastructure.driver_shape_config or {}).get(
                    "memory_in_gbs"
                ),
            )
            self.client.set_tag(
                self.active_run.info.run_id,
                "driver_ocpus",
                (self.job.infrastructure.driver_shape_config or {}).get("ocpus"),
            )
        if hasattr(self.job.infrastructure, "executor_shape_config"):
            self.client.set_tag(
                self.active_run.info.run_id,
                "executor_memory_gbs",
                (self.job.infrastructure.executor_shape_config or {}).get("memoryInGBs")
                or (self.job.infrastructure.executor_shape_config or {}).get(
                    "memory_in_gbs"
                ),
            )
            self.client.set_tag(
                self.active_run.info.run_id,
                "executor_ocpus",
                (self.job.infrastructure.executor_shape_config or {}).get("ocpus"),
            )


class Decorator(ABC):
    """The base abstract class to decorate a Job."""

    @abstractmethod
    def decorate(self, *args, **kwargs):
        pass


class RunnableInstanceDecorator(Decorator):
    """
    The base class to decorate any runnable instance.
    The runnable instance can be a DataScience/DataFlow Job.

    Attributes
    ----------
    work_dir: str
        The project working directory.
    active_run: mlflow.entities.Run
        The MLflow active run.
    project: mlflow.projects._project_spec.Project
        The MLflow project specification.
    job: ads.jobs.Job
        The ADS Job instance.
    entry_point_command: EntryPointCommand
        The project entrypoint.
    env_vars: Dict[str, Any]
        The project environment variables.
    oci_backend_config: OCIProjectBackendConfig
        The OCI backend configuration.
    tmp_dir: str
        The temporary directory.
    version: str
        For git-based projects, either a commit hash or a branch name.
    """

    def __init__(
        self,
        work_dir: str,
        active_run: Run,
        project: Project,
        job: Job,
        entry_point_command: EntryPointCommand,
        env_vars: Dict[str, Any],
        oci_backend_config: OCIProjectBackendConfig,
        tmp_dir: str,
        version: str,
    ):
        self.work_dir = work_dir
        self.active_run = active_run
        self.project = project
        self.job = job
        self.entry_point_command = entry_point_command
        self.env_vars = env_vars
        self.oci_backend_config = oci_backend_config
        self.tmp_dir = tmp_dir
        self.version = version

    def decorate(self, *args, **kwargs) -> None:
        """Decorates the instance."""
        pass


class JobDecorator(RunnableInstanceDecorator):
    """The DataScience/Dataflow job decorator."""

    def decorate(self, *args, **kwargs) -> None:
        """Decorates the job instance."""

        super().decorate(*args, **kwargs)

        # Project/Job name
        self.job.with_name(self.project.name)

        try:
            JobRuntimeDecoratorFactory.get_decorator(
                key=self.job.runtime.type,
                work_dir=self.work_dir,
                active_run=self.active_run,
                project=self.project,
                runtime=self.job.runtime,
                entry_point_command=self.entry_point_command,
                env_vars=self.env_vars,
                oci_backend_config=self.oci_backend_config,
                tmp_dir=self.tmp_dir,
                version=self.version,
            ).decorate()
        except UnsupportedJobRuntime as ex:
            logger.warn(
                f"{str(ex)} "
                "The Job will be executed with the parameters provided in the OCI template YAML."
            )


class RuntimeDecorator(Decorator):
    """
    The base class to decorate a job runtime.

    Attributes
    ----------
    work_dir: str
        The project working directory.
    active_run: mlflow.entities.Run
        The MLflow active run.
    project: mlflow.projects._project_spec.Project
        The MLflow project specification.
    runtime: ads.jobs.builders.runtimes.base.Runtime
        The ADS Job runtime.
    entry_point_command: EntryPointCommand
        The project entrypoint.
    env_vars: Dict[str, Any]
        The project environment variables.
    oci_backend_config: OCIProjectBackendConfig
        The OCI backend configuration.
    tmp_dir: str
        The temporary directory.
    version: str
        For git-based projects, either a commit hash or a branch name.
    """

    def __init__(
        self,
        work_dir: str,
        active_run: Run,
        project: Project,
        runtime: Runtime,
        entry_point_command: EntryPointCommand,
        env_vars: Dict[str, Any],
        oci_backend_config: OCIProjectBackendConfig,
        tmp_dir: str,
        version: str,
    ):
        self.work_dir = work_dir
        self.active_run = active_run
        self.project = project
        self.runtime = runtime
        self.entry_point_command = entry_point_command
        self.env_vars = env_vars
        self.oci_backend_config = oci_backend_config
        self.tmp_dir = tmp_dir
        self.version = version

    def decorate(self) -> None:

        # add freeform tags
        self.runtime.with_freeform_tag(
            **{
                **(self.runtime.freeform_tags or {}),
                **{
                    **DEFAULT_TAGS,
                    "mlflow_run_id": self.active_run.info.run_uuid,
                    "mlflow_experiment_id": self.active_run.info.experiment_id,
                    "mlflow_run_name": self.active_run.info.run_name,
                },
            }
        )

        # add environment variables
        self.runtime.with_environment_variable(
            **{
                OCIFS_IAM_TYPE: AuthType.RESOURCE_PRINCIPAL,
                **(self.env_vars or {}),
                **self.runtime.envs,
            }
        )


class ContainerRuntimeDecorator(RuntimeDecorator):
    """Container runtime decorator."""

    def decorate(self, *args, **kwargs):
        super().decorate(*args, **kwargs)
        self.runtime.with_cmd(self.entry_point_command.cmd)


class DataflowRuntimeDecorator(RuntimeDecorator):
    """DataFlow runtime decorator."""

    def decorate(self, *args, **kwargs):
        super().decorate(*args, **kwargs)

        self.runtime.with_script_uri(
            os.path.join(
                self.work_dir.rstrip("/"), self.entry_point_command.entry_point
            )
        ).with_argument(*self.entry_point_command.args)

        # propagate environment variables to the runtime config
        runtime_config = self.runtime.configuration or dict()

        existing_env_keys = {
            key.upper()
            .replace("SPARK.EXECUTORENV.", "")
            .replace("SPARK.DRIVERENV.", "")
            for key in runtime_config
            if "SPARK.EXECUTORENV" in key.upper() or "SPARK.DRIVERENV" in key.upper()
        }

        for env_key, env_value in (self.env_vars or {}).items():
            if env_key.upper() not in existing_env_keys:
                runtime_config[f"spark.driverEnv.{env_key}"] = env_value

        self.runtime.with_configuration(runtime_config)


class ScriptRuntimeDecorator(RuntimeDecorator):
    """Script runtime decorator."""

    def decorate(self, *args, **kwargs):
        super().decorate(*args, **kwargs)

        self.runtime.with_source(
            self.work_dir,
            entrypoint=os.path.join(
                os.path.basename(self.work_dir.rstrip("/")),
                self.entry_point_command.entry_point,
            ),
        ).with_argument(*self.entry_point_command.args)


class PythonRuntimeDecorator(RuntimeDecorator):
    """Python runtime decorator."""

    def decorate(self, *args, **kwargs):
        super().decorate(*args, **kwargs)

        self.runtime.with_source(
            self.work_dir,
            entrypoint=os.path.join(
                self.entry_point_command.entry_point,
            ),
        ).with_argument(*self.entry_point_command.args).with_working_dir(
            os.path.basename(self.work_dir.rstrip("/"))
        )


class GitPythonRuntimeDecorator(RuntimeDecorator):
    """GytPython runtime decorator."""

    def decorate(self, *args, **kwargs):
        super().decorate(*args, **kwargs)
        self.runtime.with_source(
            url=self.oci_backend_config.project_uri,
            branch=self.runtime.branch,
            commit=self.version,
            secret_ocid=self.runtime.ssh_secret_ocid,
        )
        self.runtime.with_entrypoint(self.entry_point_command.entry_point)
        self.runtime.with_argument(*self.entry_point_command.args)


class NotebookRuntimeDecorator(RuntimeDecorator):
    """Notebook runtime decorator."""

    def decorate(self, *args, **kwargs):
        super().decorate(*args, **kwargs)
        self.runtime.with_source(
            self.work_dir,
            notebook=os.path.join(
                self.entry_point_command.entry_point,
            ),
            encoding=self.runtime.notebook_encoding or "utf-8",
        ).with_argument(*self.entry_point_command.args)


class DataFlowNotebookRuntimeDecorator(RuntimeDecorator):
    """Notebook runtime decorator."""

    def decorate(self, *args, **kwargs):
        super().decorate(*args, **kwargs)
        self.runtime.with_notebook(
            path=os.path.join(
                self.work_dir.rstrip("/"),
                self.entry_point_command.entry_point,
            ),
            encoding=self.runtime.notebook_encoding or "utf-8",
        ).with_argument(*self.entry_point_command.args)


class DecoratorFactory:
    """Base factory for the decorator."""

    _MAP = {}


class RunnableInstanceDecoratorFactory(DecoratorFactory):
    """Runnable instance decorator factory."""

    _MAP = {Job().kind: JobDecorator}

    @classmethod
    def get_decorator(cls, key: str, *args, **kwargs):
        if key not in cls._MAP:
            raise UnsupportedRunnableInstance(key)
        return cls._MAP[key](*args, **kwargs)


class JobRuntimeDecoratorFactory(DecoratorFactory):
    """Job runtime decorator factory."""

    _MAP = {
        ContainerRuntime().type: ContainerRuntimeDecorator,
        ScriptRuntime().type: ScriptRuntimeDecorator,
        PythonRuntime().type: PythonRuntimeDecorator,
        NotebookRuntime().type: NotebookRuntimeDecorator,
        DataFlowRuntime().type: DataflowRuntimeDecorator,
        DataFlowNotebookRuntime().type: DataFlowNotebookRuntimeDecorator,
        GitPythonRuntime().type: GitPythonRuntimeDecorator,
    }

    @classmethod
    def get_decorator(cls, key: str, *args, **kwargs):
        if key not in cls._MAP:
            raise UnsupportedJobRuntime(key)
        return cls._MAP[key](*args, **kwargs)
