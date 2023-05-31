##########
Quickstart
##########

`MLflow <https://www.mlflow.org/>`_ is a popular open source platform to manage the ML lifecycle, including
experimentation, reproducibility, deployment, and a central model registry. MLflow currently offers four components:

 - MLflow Tracking *(experiment tracking)*
 - MLflow Projects *(code packaging format for reproducible runs using Conda on Data Science Jobs and Data Flow)*
 - MLflow Models *(package models for deployment in real time scoring, and batch scoring)*
 - Model Registry *(manage models)*

Using MLflow with `Oracle Cloud Infrastructure (OCI) Data Science <https://www.oracle.com/artificial-intelligence/data-science/>`_ you will first need to install the Oracle OCI MLflow plugin:

.. note::

  The OCI MLflow plugin will also install (if necessary) the ``mlflow`` and ``oracle-ads`` packages

  .. list-table::
    :widths: 25 75
    :header-rows: 1
    :align: left

    * - Package Name
      - Latest Version
    * - MLflow
      - .. image:: https://img.shields.io/pypi/v/mlflow.svg?style=for-the-badge&logo=pypi&logoColor=white
    * - oracle-ads
      - .. image:: https://img.shields.io/pypi/v/oracle-ads.svg?style=for-the-badge&logo=pypi&logoColor=white


- Install the ``oci-mlflow`` plugin

  ..  code-block:: shell

    pip install oci-mlflow

- Test ``oci-mlflow`` plugin setup

  ..  code-block:: shell

    mlflow deployments help -t oci-datascience


Background reading to understand the concepts of MLflow and OCI Data Science:

- Getting started with  `OCI Data Science Jobs <https://docs.oracle.com/en-us/iaas/data-science/using/jobs-about.htm>`__
- Getting started with  `Oracle Accelerated Data Science SDK <https://accelerated-data-science.readthedocs.io/en/latest/index.html>`__ to simplify `creating <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/jobs/data_science_job.html#define-a-job>`__ and `running <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/jobs/data_science_job.html#run-a-job-and-monitor-outputs>`__ Jobs
- Getting started with  `Data Science Environments <https://docs.oracle.com/en-us/iaas/data-science/using/conda_environ_list.htm>`__
- Getting started with  `Custom Conda Environments <https://docs.oracle.com/en-us/iaas/data-science/using/conda_create_conda_env.htm>`__

**Authentication and Policies:**

- Getting started with `OCI Data Science Policies <https://docs.oracle.com/en-us/iaas/data-science/using/policies.htm>`__
- `API Key-Based Authentication <https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm#sdk_authentication_methods_api_key>`__ - ``api_key``
- `Resource Principal Authentication <https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm#sdk_authentication_methods_resource_principal>`__ - ``resource_principal``
- `Instance Principal Authentication <https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm#sdk_authentication_methods_instance_principaldita>`__ - ``instance_principal``

**OCI Integration Points**

The ``oci_mlflow`` plugin enables OCI users to use OCI resources to manage their machine learning usecase life cycle. This
table below provides the mapping between the MLflow features and the OCI resources that are used.

.. note::
  .. list-table::
    :widths: 15 10
    :header-rows: 1
    :align: left

    * - MLflow Use Case
      - OCI Resource
    * - User running machine learning experiments on notebook, logs model artifacts, model performance etc
      - Data Science Jobs, Object Storage, MySQL
    * - Batch workloads using spark
      - Data Flow, Object Storage, MySQL
    * - Model Deployment
      - Data Science Model Deployment
    * - User running machine learning experiments on notebook,  logs model artifacts, model performance etc
      - Object Storage, MySQL
