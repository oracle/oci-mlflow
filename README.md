# OCI Mlflow Plugin

[![PyPI](https://img.shields.io/pypi/v/oci-mlflow.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/oci-mlflow/) [![Python](https://img.shields.io/pypi/pyversions/oci-mlflow.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/oci-mlflow/)

The OCI MLflow plugin enables OCI users to use OCI resources to manage their machine learning use case life cycle. This table below provides the mapping between the MLflow features and the OCI resources that are used.

| MLflow Use Case    | OCI Resource |
| -------- | ------- |
| User running machine learning experiments on notebook, logs model artifacts, model performance etc  | Data Science Jobs, Object Storage, MySQL |
| Batch workloads using spark | Data Flow, Object Storage, MySQL |
| Model Catalog | Data Science Model Catalog |
| Model Deployment    | Data Science Model Deployment |
| User running machine learning experiments on notebook, logs model artifacts, model performance etc    | Object Storage, MySQL |


## Installation

To install the `oci-mlflow` plugin call -

```bash
  python3 -m pip install oci-mlflow
```

To test the `oci-mlflow` plugin call -

```bash
  mlflow deployments help -t oci-datascience
```

## Documentation
  - [OCI MLflow Documentation](https://oci-mlflow.readthedocs.io/en/latest/index.html)
  - [Getting started with Oracle Accelerated Data Science SDK](https://accelerated-data-science.readthedocs.io/en/latest/index.html)
  - [Getting started with OCI Data Science Jobs](https://docs.oracle.com/en-us/iaas/data-science/using/jobs-about.htm)
  - [Getting started with Data Science Environments](https://docs.oracle.com/en-us/iaas/data-science/using/conda_environ_list.htm)
  - [Getting started with Custom Conda Environments](https://docs.oracle.com/en-us/iaas/data-science/using/conda_create_conda_env.htm)
  - [Getting started with Model Catalog](https://docs.oracle.com/en-us/iaas/data-science/using/models-about.htm)
  - [Getting started with Model Deployment](https://docs.oracle.com/en-us/iaas/data-science/using/model-dep-about.htm)
  - [Oracle AI & Data Science Blog](https://blogs.oracle.com/ai-and-datascience/)
  - [OCI Documentation](https://docs.oracle.com/en-us/iaas/data-science/using/data-science.htm)

## Examples
### Running MLflow projects on the OCI `Data Science jobs` and `Data Flow applications` -

```bash
export MLFLOW_TRACKING_URI=<tracking server url>
mlflow run . --experiment-name My-Experiment --backend oci-datascience --backend-config ./oci-datascience-config.json
```

### Deploying MLflow models to the OCI Model Deployments -

```bash
mlflow deployments help -t oci-datascience

export MLFLOW_TRACKING_URI=<tracking server url>

mlflow deployments create --name <model deployment name> -m models:/<registered model name>/<model version> -t oci-datascience --config deploy-config-file=deployment_specification.yaml
```


## Contributing

This project welcomes contributions from the community. Before submitting a pull request, please[review our contribution guide](./CONTRIBUTING.md)

Find Getting Started instructions for developers in [README-development.md](https://github.com/oracle/oci-mlflow/blob/main/README-development.md)

## Security

Consult the security guide [SECURITY.md](https://github.com/oracle/oci-mlflow/blob/main/SECURITY.md) for our responsible security vulnerability disclosure process.

## License

Copyright (c) 2023 Oracle and/or its affiliates. Licensed under the [Universal Permissive License v1.0](https://oss.oracle.com/licenses/upl/)
