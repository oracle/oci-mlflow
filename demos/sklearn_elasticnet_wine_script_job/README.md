## Run MLflow project on the Data Science job
---

This demo shows how to run an MLflow project locally as well as on the Data Science job within a Python runtime. This directory contains only the configuration files which are necessary to run the project on the Data Science job. The project by itself will be downloaded form the [GIT](https://github.com/mlflow/mlflow-example) repository. The project trains a linear regression model on the UC Irvine Wine Quality Dataset.

## Prerequisites
- First, install MLflow library
  ```
  pip install mlflow
  ```
- Set the tracking server endpoint.
   ```
   export MLFLOW_TRACKING_URI=<http://ip:port>
   ```
- Install the oci-mlflow package
  ```
  pip install oci-mlflow
  ```

## Running this example locally
The project will be executed on the local instance and the result will be added to the tracking URI specified above.
 - Run the example project using CLI

    ```
    mlflow run https://github.com/mlflow/mlflow#examples/sklearn_elasticnet_wine --experiment-name My_Experiment
    ```
 - Run the example project using SDK
    ```
    import mlflow

    mlflow.set_tracking_uri("<http://ip:port>")

    mlflow.run("https://github.com/mlflow/mlflow#examples/sklearn_elasticnet_wine",
      experiment_name="My_Experiment",
    )
    ```

## Running this example on the Data Science job
To run this example on the Data Science job, the custom conda environment was prepared and published to the Object Storage bucket. The custom conda environment contains all the required packages provided in the [conda.yaml](https://github.com/mlflow/mlflow-example/blob/master/conda.yaml) as well as the `oci-mlflow` library. The `generalml_p38_cpu_v1` service conda environment was used as a base environment for the custom one.
- Install the OCI MLflow package
  ```
  pip install oci-mlflow
  ```
- Prepare and publish a custom conda environment which should contain `mlflow`, `oci-mlfow` and all libraries from the [conda.yaml](https://github.com/mlflow/mlflow-example/blob/master/conda.yaml)

- Prepare the OCI config, which is a JSON file containing the authentication information and also path to the job configuration YAML file. Note, that the project folder already contains the all necessary files to run this example.
  ```
  {
    "oci_auth": "api_key",
    "oci_job_template_path": "./oci-datascience-template.yaml"
  }
  ```
- Prepare the job configuration file.
  ```
  kind: job
  name: "{Job name. For MLflow, it will be replaced with the Project name}"
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
        shapeName: VM.Standard.E3.Flex
        shapeConfigDetails:
          memoryInGBs: 20
          ocpus: 2
      type: dataScienceJob
    runtime:
      kind: runtime
      spec:
        args: []
        conda:
          type: published
          uri: <oci://bucket@namespace/prefix>
        env:
        - name: TEST
          value: TEST_VALUE
        entrypoint: "{Entry point script. For the MLFlow will be replaced with the CMD}"
        scriptPathURI: "{Path to the script. For the MLFlow will be replaced with path to the project}"
      type: python

  ```
 - Run the example project using CLI

    ```
    mlflow run https://github.com/mlflow/mlflow#examples/sklearn_elasticnet_wine --experiment-name My_Experiment --backend oci-datascience --backend-config ./oci-datascience-config.json
    ```
 - Run the example project using SDK
    ```
    import mlflow

    mlflow.set_tracking_uri("<http://ip:port>/")

    mlflow.run("https://github.com/mlflow/mlflow#examples/sklearn_elasticnet_wine",
      experiment_name="My_Experiment",
      backend="oci-datascience",
      backend_config="oci-datascience-config.json"
    )
    ```
