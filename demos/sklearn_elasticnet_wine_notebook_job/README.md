## Run MLflow project on the Data Science job
---

This demo shows how to run an MLflow project on the Data Science job within a Notebook runtime. This directory contains an MLflow project that trains a linear regression model on the UC Irvine Wine Quality Dataset.

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

## Running this example on the Data Science job
To run this example on the Data Science job, the custom conda environment was prepared and published to the Object Storage bucket. The `generalml_p38_cpu_v1` service conda environment was used as a base environment for the custom one.

- Install the OCI MLflow package
  ```
  pip install oci-mlflow
  ```
- Prepare the OCI config, which is a JSON file containing the authentication information and also path to the job configuration YAML file
  ```
  {
    "oci_auth": "api_key",
    "oci_job_template_path": "./oci-datascience-template.yaml"
  }
  ```
- Prepare the job configuration file
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
        env:
        - name: TEST
          value: TEST_VALUE
        entrypoint: "{Entry point notebook. For MLflow, it will be replaced with the CMD}"
        source: "{Path to the source code directory. For MLflow, it will be replaced with path to the project}"
        notebookEncoding: utf-8
      type: notebook
  ```

 - Run the example project using CLI

    ```
    mlflow run . --experiment-name My_Experiment --backend oci-datascience --backend-config ./oci-datascience-config.json
    ```

 - Run the example project using SDK
    ```
    import mlflow

    mlflow.set_tracking_uri("<http://ip:port>")

    mlflow.run(".",
      experiment_name="MyExperiment",
      backend="oci-datascience",
      backend_config="oci-datascience-config.json"
    )
    ```
