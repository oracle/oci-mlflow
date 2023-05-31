########
Projects
########

An `MLflow project <https://mlflow.org/docs/latest/projects.html>`__ is a format for packaging data science code in a reusable and reproducible way. The MLflow Projects component includes an API and command-line tools for running projects, which also integrate with the Tracking component to automatically record the parameters and git commit of your source code for reproducibility. This document describes the steps that need to be done to run MLflow projects on Oracle Cloud Infrastructure.

Data Science Jobs
-----------------

The examples demonstrated in this section show running the MLflow projects on the OCI Data Science jobs within different runtimes supported by the service.
All demonstrated examples were taken from the `MLflow official GitHub repository <https://github.com/mlflow/mlflow/tree/master/examples>`__ .


.. _jobs_prerequisites:

.. admonition:: Prerequisites
  :class: note

  - Based on the ``General Machine Learning for CPUs on Python 3.8 (generalml_p38_cpu_v1)`` create and publish a `custom conda environment <https://docs.oracle.com/en-us/iaas/data-science/using/conda_create_conda_env.htm>`__ with additional libraries:

    - mlflow
    - oci-mlflow


Data Science Config
===================

The OCI Data Science config is a JSON file contains the authentication information as well as the path to the job template YAML file.

.. tabs::

    .. code-tab:: json

        {
          "oci_job_template_path": "{work_dir}/oci-datascience-template.yaml",
          "oci_auth": "api_key",
          "oci_config_path": "~/.oci/config",
          "oci_profile": "DEFAULT"
        }

The ``{work_dir}`` can be used to point out that the YAML template located inside the project directory. It will be auto replaced with the absolute path to the project. However for the cases when YAML template cannot be placed in the project folder, the absolute or relative path can be used instead.

*Supported authentication types:*

 - `API Key-Based Authentication <https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm#sdk_authentication_methods_api_key>`__ - ``api_key``
 - `Resource Principal Authentication <https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm#sdk_authentication_methods_resource_principal>`__ - ``resource_principal``
 - `Instance Principal Authentication <https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm#sdk_authentication_methods_instance_principaldita>`__ - ``instance_principal``


Data Science Job Template
=========================

The template file contains the information about the infrastructure on which a Data Science job should be run, and also the runtime information. More details can be found in the `ADS documentation <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/jobs/data_science_job.html>`__. The template file is divided into two main sections: ``infrastructure`` and ``runtime``.

Data Science Job Infrastructure
###############################

The Data Science job infrastructure allows specifying the configuration of the job instance. It includes such information as:

 - Compartment ID
 - Project ID
 - Subnet ID
 - Compute Shape
 - Block Storage Size
 - Log Group ID
 - Log ID

More details about job infrastructure can be found in the `ADS documentation <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/jobs/infra_and_runtime.html#infrastructure-and-runtime>`__


.. tabs::

    .. code-tab:: yaml

        infrastructure:
          kind: infrastructure
          spec:
            blockStorageSize: 50
            subnetId: ocid1.subnet.oc1.iad..<unique_ID>
            compartmentId: ocid1.compartment.oc1..<unique_ID>
            projectId: ocid1.datascienceproject.oc1.iad..<unique_ID>
            logGroupId: ocid1.loggroup.oc1.iad..<unique_ID>
            logId: ocid1.log.oc1.iad..<unique_ID>
            shapeConfigDetails:
              memoryInGBs: 20
              ocpus: 2
            shapeName: VM.Standard.E3.Flex
          type: dataScienceJob


Data Science Job Runtime
########################

The `runtime <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/jobs/infra_and_runtime.html#runtime>`__ of a job defines the source code of your workload, environment variables, CLI arguments, and other configurations for the environment to run the workload. You will not work with the runtimes directly but will have to specify a YAML definition of the runtime to run an MLflow project on the Data Science job.

Depending on the source code, we do provide different types of runtime for defining a data science job:

    - `PythonRuntime <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/jobs/run_python.html>`__ for Python code stored locally, OCI object storage, or other remote location supported by fsspec.
    - `NotebookRuntime <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/jobs/run_notebook.html>`__ for a single Jupyter notebook stored locally, OCI object storage, or other remote location supported by fsspec.
    - `ContainerRuntime <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/jobs/run_container.html>`__ for container images.

.. tabs::

    .. code-tab:: yaml
      :caption: PythonRuntime

        runtime:
          kind: runtime
          spec:
            args: []
            conda:
              type: published
              uri: <oci://bucket@namespace/prefix>
            env:
            - name: http_proxy
              value: <http://ip:port>
            entrypoint: "{Entry point script. For the MLflow will be replaced with the CMD}"
            scriptPathURI: "{Path to the script. For the MLflow will be replaced with path to the project}"
          type: python

    .. code-tab:: yaml
      :caption: NotebookRuntime

        runtime:
          kind: runtime
          spec:
            args: []
            conda:
              type: published
              uri: <oci://bucket@namespace/prefix>
            env:
            - name: http_proxy
              value: <http://ip:port>
            entrypoint: "{Entry point notebook. For MLflow, it will be replaced with the CMD}"
            source: "{Path to the source code directory. For MLflow, it will be replaced with path to the project}"
            notebookEncoding: utf-8
          type: notebook

    .. code-tab:: yaml
      :caption: ContainerRuntime

        runtime:
          kind: runtime
          spec:
            image: <iad.ocir.io/namespace/image_name:version>
            cmd: "{Container CMD. For MLflow, it will be replaced with the Project CMD}"
            entrypoint:
            - bash
            - --login
            - -c
          type: container

Running MLflow project within PythonRuntime
===========================================

This example demonstrates an MLflow project that trains a linear regression model on the UC Irvine Wine Quality Dataset. To run this example on the Data Science job, the custom conda environment needs to be prepared and published to the Object Storage bucket. The project can be run from source or by using GIT link.

- To run project from the source, pull a `sklearn_elasticnet_wine <https://github.com/mlflow/mlflow/tree/master/examples/sklearn_elasticnet_wine>`__ project form the GitHub repository. If you want to run the project with GIT URI, create a ``sklearn_elasticnet_wine`` folder.

- Prepare and publish a `custom conda environment <https://docs.oracle.com/en-us/iaas/data-science/using/conda_create_conda_env.htm>`__. The libraries listed below need to be installed in your custom conda environment. This section can be skipped if you already prepared the custom conda environment following the prerequisites section in the beginning of the documentation.

  - scikit-learn
  - mlflow
  - pandas
  - oci-mlflow

- Prepare a ``oci-datascience-config.json`` file containing the authentication information and path to the job configuration YAML file.

  .. tabs::

      .. code-tab:: json

          {
            "oci_auth": "api_key",
            "oci_job_template_path": "oci-datascience-template.yaml"
          }

  Copy the ``oci-datascience-config.json`` file to the ``sklearn_elasticnet_wine`` folder.

- Prepare a ``oci-datascience-template.yaml`` job configuration file.

  .. tabs::

      .. code-tab:: yaml

          kind: job
          name: "{Job name. For the MLflow will be replaced with the Project name}"
          spec:
            infrastructure:
              kind: infrastructure
              spec:
                blockStorageSize: 50
                subnetId: ocid1.subnet.oc1.iad..<unique_ID>
                compartmentId: ocid1.compartment.oc1..<unique_ID>
                projectId: ocid1.datascienceproject.oc1.iad..<unique_ID
                logGroupId: ocid1.loggroup.oc1.iad..<unique_ID>
                logId: ocid1.log.oc1.iad..<unique_ID>
                shapeConfigDetails:
                  memoryInGBs: 20
                  ocpus: 2
                shapeName: VM.Standard.E3.Flex
              type: dataScienceJob
            runtime:
              kind: runtime
              spec:
                args: []
                conda:
                  type: published
                  uri: <oci://bucket@namespace/prefix>
                entrypoint: "{Entry point script. For the MLflow will be replaced with the CMD}"
                scriptPathURI: "{Path to the script. For the MLflow will be replaced with path to the project}"
              type: python

  Copy the ``oci-datascience-template.yaml`` file to the ``sklearn_elasticnet_wine`` folder.

- Run the project from the source

  .. tabs::

    .. code-tab:: shell
      :caption: CLI

        cd ~/sklearn_elasticnet_wine
        export MLFLOW_TRACKING_URI=<tracking_uri>
        mlflow run . --experiment-name My_Experiment --backend oci-datascience --backend-config ./oci-datascience-config.json

    .. code-tab:: python
      :caption: SDK

        import mlflow

        mlflow.set_tracking_uri("<tracking_uri>i")

        mlflow.run(
            ".",
            parameters={"alpha": 0.7, "l1-ratio": 0.06},
            experiment_name="My_Experiment",
            backend="oci-datascience",
            backend_config="oci-datascience-config.json",
        )

- Run the project with GIT URI

  .. tabs::

    .. code-tab:: shell
      :caption: CLI

        cd ~/sklearn_elasticnet_wine
        export MLFLOW_TRACKING_URI=<tracking_uri>
        mlflow run https://github.com/mlflow/mlflow#examples/sklearn_elasticnet_wine --experiment-name My_Experiment --backend oci-datascience --backend-config ./oci-datascience-config.json

    .. code-tab:: python
      :caption: SDK

        import mlflow

        mlflow.set_tracking_uri("<tracking_uri>i")

        mlflow.run(
            "https://github.com/mlflow/mlflow#examples/sklearn_elasticnet_wine",
            experiment_name="My_Experiment",
            backend="oci-datascience",
            backend_config="oci-datascience-config.json",
        )

Running MLflow project within NotebookRuntime
=============================================

This example demonstrates an MLflow project that trains a linear regression model on the UC Irvine Wine Quality Dataset. To run this example on the Data Science job, the custom conda environment needs to be prepared and published to the Object Storage bucket.


- Download a `sklearn_elasticnet_wine <https://github.com/mlflow/mlflow/tree/master/examples/sklearn_elasticnet_wine>`__ project form the GitHub repository.

- Prepare and publish a `custom conda environment <https://docs.oracle.com/en-us/iaas/data-science/using/conda_create_conda_env.htm>`__. The libraries listed below need to be installed in your custom conda environment.

    - scikit-learn
    - mlflow
    - pandas
    - oci-mlflow


- Prepare a ``oci-datascience-config.json`` file containing the authentication information and path to the job configuration YAML file.

  .. tabs::

      .. code-tab:: json

          {
            "oci_auth": "api_key",
            "oci_job_template_path": "{work_dir}/oci-datascience-template.yaml"
          }

  Copy the ``oci-datascience-config.json`` file to the ``sklearn_elasticnet_wine`` folder.

- Prepare a ``oci-datascience-template.yaml`` job configuration file.

  .. tabs::

      .. code-tab:: yaml

          kind: job
          name: "{Job name. For the MLflow will be replaced with the Project name}"
          spec:
            infrastructure:
              kind: infrastructure
              spec:
                blockStorageSize: 50
                subnetId: ocid1.subnet.oc1.iad..<unique_ID>
                compartmentId: ocid1.compartment.oc1..<unique_ID>
                projectId: ocid1.datascienceproject.oc1.iad..<unique_ID>
                logGroupId: ocid1.loggroup.oc1.iad..<unique_ID>
                logId: ocid1.log.oc1.iad..<unique_ID>
                shapeConfigDetails:
                  memoryInGBs: 20
                  ocpus: 2
                shapeName: VM.Standard.E3.Flex
              type: dataScienceJob
            runtime:
              kind: runtime
              spec:
                args: []
                conda:
                  type: published
                  uri: <oci://bucket@namespace/prefix>
                entrypoint: "{Entry point notebook. For MLflow, it will be replaced with the CMD}"
                source: "{Path to the source code directory. For MLflow, it will be replaced with path to the project}"
                notebookEncoding: utf-8
              type: notebook

  Copy the ``oci-datascience-template.yaml`` file to the ``sklearn_elasticnet_wine`` folder.

- Update the ``MLproject`` file with the content provided below

  .. tabs::

      .. code-tab:: yaml

          name: tutorial

          entry_points:
            main:
              command: "train.ipynb"

- Run the project

  .. tabs::

    .. code-tab:: shell
      :caption: CLI

        cd ~/sklearn_elasticnet_wine
        export MLFLOW_TRACKING_URI=<tracking_uri>
        mlflow run . --experiment-name My_Experiment --backend oci-datascience --backend-config ./oci-datascience-config.json

    .. code-tab:: python
      :caption: SDK

        import mlflow
        mlflow.set_tracking_uri(<tracking_uri>)

        mlflow.run(".",
          experiment_name="My_Experiment",
          backend="oci-datascience",
          backend_config="oci-datascience-config.json"
        )

Running MLflow project within ContainerRuntime
==============================================

This example demonstrates an MLflow project that trains a linear regression model on the UC Irvine Wine Quality Dataset. In the first step, you will need to download the `docker <https://github.com/mlflow/mlflow/tree/master/examples/docker>`__ example from the MLflow official GitHub repository and go through the `README.rst <https://github.com/mlflow/mlflow/blob/master/examples/docker/README.rst>`__ document provided within the project. The project uses a Docker image to capture the dependencies needed to run training code. Running a project in a Docker environment (as opposed to conda) allows for capturing non-Python dependencies, e.g. Java libraries. Once all steps from the `README.rst <https://github.com/mlflow/mlflow/blob/master/examples/docker/README.rst>`__ are passed and the project can be run on the local environment, follow the steps below to run the project on the OCI Data Science jobs.


- Download a `docker <https://github.com/mlflow/mlflow/tree/master/examples/docker>`__ project form the GitHub repository and place the code to the ``sklearn_elasticnet_wine`` folder.
- Prepare a docker image following the steps from the `README.rst <https://github.com/mlflow/mlflow/blob/master/examples/docker/README.rst>`__. Add into the docker file the ``oci-mlflow`` library.

  .. tabs::

      .. code-tab:: shell

          FROM python:3.8

          RUN pip install mlflow \
              && pip install oci \
              && pip install oracle-ads \
              && pip install numpy \
              && pip install scipy \
              && pip install pandas \
              && pip install scikit-learn \
              && pip install cloudpickle \
              && pip install oci-mlflow

- Build and publish the image to the OCI container registry

  .. tabs::

      .. code-tab:: shell

          docker tag mlflow-docker-example:<your_tag> <registry_path>/mlflow-docker-example:latest && \
          docker push <registry_path>/mlflow-docker-example:latest


- Prepare a ``oci-datascience-config.json`` file containing the authentication information and path to the job configuration YAML file.

  .. tabs::

      .. code-tab:: json

          {
            "oci_auth": "api_key",
            "oci_job_template_path": "{work_dir}/oci-datascience-template.yaml"
          }

  Copy the ``oci-datascience-config.json`` file to the ``sklearn_elasticnet_wine`` folder.

- Prepare a ``oci-datascience-template.yaml`` job configuration file.

  .. tabs::

      .. code-tab:: yaml

          kind: job
          spec:
            name: "{Job name. For the MLflow will be replaced with the Project name}"
            infrastructure:
              kind: infrastructure
              spec:
                blockStorageSize: 50
                subnetId: ocid1.subnet.oc1.iad..<unique_ID>
                compartmentId: ocid1.compartment.oc1..<unique_ID>
                projectId: ocid1.datascienceproject.oc1.iad..<unique_ID>
                logGroupId: ocid1.loggroup.oc1.iad..<unique_ID>
                logId: ocid1.log.oc1.iad..<unique_ID>
                shapeName: VM.Standard.E3.Flex
                shapeConfigDetails:
                  memoryInGBs: 20
                  ocpus: 2
              type: dataScienceJob
            runtime:
              type: container
              kind: runtime
              spec:
                image: <iad.ocir.io/realm/container:tag>
                cmd: "{Container CMD. For the MLflow will be replaced with the Project CMD}"
                entrypoint:
                - bash
                - --login
                - -c

  Copy the ``oci-datascience-template.yaml`` file to the ``sklearn_elasticnet_wine`` folder.

- Run the project

  .. tabs::

    .. code-tab:: shell
      :caption: CLI

        cd ~/sklearn_elasticnet_wine
        export MLFLOW_TRACKING_URI=<tracking_uri>
        mlflow run . --experiment-name My_Experiment --backend oci-datascience --backend-config ./oci-datascience-config.jsonjson

    .. code-tab:: python
      :caption: SDK

        import mlflow
        mlflow.set_tracking_uri(<tracking_uri>)

        mlflow.run(".",
          experiment_name="My_Experiment",
          parameters={"alpha": 0.7},
          backend="oci-datascience",
          backend_config="oci-datascience-config.json"
        )

Data Flow Applications
----------------------

The examples demonstrated in this section show how to run MLflow projects on a `Data Flow remote Spark cluster <https://docs.oracle.com/en-us/iaas/data-flow/using/dfs_getting_started.htm>`__. All examples were taken from the `MLflow <https://github.com/mlflow/mlflow/tree/master/examples>`__ official repository.

.. _dataflow_prerequisites:

.. admonition:: Prerequisites
  :class: note

  - Based on the ``PySpark 3.2 and Data Flow (pyspark32_p38_cpu_v2)`` create and publish a `custom conda environment <https://docs.oracle.com/en-us/iaas/data-science/using/conda_create_conda_env.>`__ with additional libraries:
    - mlflow
    - oci-mlflow

Running MLflow project within DataflowRuntime
=============================================

This example demonstrates an MLflow project that trains a logistic regression model on the Iris dataset. To run this example on the Data Flow cluster, the custom conda environment needs to be prepared and published to the Object Storage bucket.

- Download a `pyspark_ml_autologging <https://github.com/mlflow/mlflow/tree/master/examples/pyspark_ml_autologging>`__ project form the GitHub repository.

- Prepare a ``oci-datascience-config.json`` file containing the authentication information and path to the job configuration YAML file.

  .. tabs::

      .. code-tab:: yaml

          {
            "oci_auth": "api_key",
            "oci_job_template_path": "{work_dir}/oci-datascience-template.yaml"
          }

  Copy the ``oci-datascience-config.json`` file to the ``pyspark_ml_autologging`` folder.

- Prepare a ``oci-datascience-template.yaml`` job configuration file.

  .. tabs::

      .. code-tab:: yaml

          kind: job
          name: "{DataFlow application name. For the MLflow will be replaced with the Project name}"
          spec:
            infrastructure:
              kind: infrastructure
              spec:
                compartmentId: ocid1.compartment.oc1..<unique_ID>
                driverShape: VM.Standard.E4.Flex
                driverShapeConfig:
                  memory_in_gbs: 32
                  ocpus: 2
                executorShape: VM.Standard.E4.Flex
                executorShapeConfig:
                  memory_in_gbs: 32
                  ocpus: 2
                language: PYTHON
                logsBucketUri: <oci://bucket@namespace>
                numExecutors: 1
                sparkVersion: 3.2.1
                privateEndpointId: ocid1.dataflowprivateendpoint.oc1.iad..<unique_ID>
              type: dataFlow
            runtime:
              kind: runtime
              spec:
                configuration:
                  spark.driverEnv.MLFLOW_TRACKING_URI: <http://FQDN-address-of-the-container-instance:5000>
                conda:
                  type: published
                  uri: <oci://bucket@namespace/prefix>
                condaAuthType: resource_principal
                scriptBucket: <oci://bucket@namespace/prefix>
                scriptPathURI: "{Path to the executable script. For the MLflow will be replaced with the CMD}"
                overwrite: True
              type: dataFlow

  In the config file, we do also specify a Private Endpoint (``privateEndpointId``) which allows the Data Flow cluster to reach out to the tracking server URI (in case of the tracking server deployed in the private network). However, the private endpoint is not required for the case when the tracking server has a public Ip address. More details about the Private Endpoint can be found in the official `documentation <https://docs.oracle.com/en-us/iaas/data-flow/using/private-network.>`__. We do also specify a ``spark.driverEnv.MLFLOW_TRACKING_URI`` property, which is only required in case of using a private endpoint and should be an FQDN of the container instance.

  Copy the ``oci-datascience-template.yaml`` file to the ``pyspark_ml_autologging`` folder.

- Create an ``MLproject`` file in the ``pyspark_ml_autologging`` folder.

  .. tabs::

    .. code-tab:: yaml

        name: mlflow-project-dataflow-application

        entry_points:
          main:
            command: "logistic_regression.py"

- Run the example project

  .. tabs::

    .. code-tab:: shell
      :caption: CLI

      cd ~/pyspark_ml_autologging
      export MLFLOW_TRACKING_URI=<tracking_uri>
      mlflow run . --experiment-name My_Experiment --backend oci-datascience --backend-config ./oci-datascience-config.json

    .. code-tab:: python
      :caption: SDK

      import mlflow

      mlflow.set_tracking_uri(<tracking_uri>)

      mlflow.run(".",
        experiment_name="My_Experiment",
        backend="oci-datascience",
        backend_config="oci-datascience-config.json"
      )
