## Run MLflow project on the Data Flow cluster
---

This demo shows how to run an MLflow project on the Data Flow cluster. This directory contains an MLflow project file that trains a logistic regression model on the Iris dataset.

## Prerequisites
- First, install MLflow library
  ```
  pip install mlflow
  ```
- Set the tracking server endpoint
   ```
   export MLFLOW_TRACKING_URI=<http://ip:port>
   ```
- Install the oci-mlflow package
  ```
  pip install oci-mlflow
  ```

## Running this example on the Data Flow cluster
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
  name: "{DataFlow application name. For MLflow, it will be replaced with the Project name}"
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
        privateEndpointId: ocid1.dataflowprivateendpoint.oc1..<unique_ID>
      type: dataFlow
    runtime:
      kind: runtime
      spec:
        configuration:
          spark.driverEnv.MLFLOW_TRACKING_URI: <http://tracking_uri.com:5000>
        conda:
          type: published
          uri: oci://bucket@namespace/prefix
        condaAuthType: resource_principal
        scriptBucket: <oci://bucket@namespace/prefix>
        scriptPathURI: "{Path to the executable script. For MLflow, it will be replaced with the CMD}"
        overwrite: True
      type: dataFlow
  ```
  In the config file we also specify a Private Endpoint, which allows the cluster to reach out the tracking server URI, in case if tracking server deployed in the private network. However the private endpoint is not necessary for the case when the tracking server has public Ip address. More details about the Private Endpoint can be found in the official [documentation](https://docs.oracle.com/en-us/iaas/data-flow/using/private-network.htm).

 - Run the example project using CLI
    ```
    mlflow run . --param-list seed=24 --experiment-name My_Experiment --backend oci-datascience --backend-config ./oci-datascience-config.json
    ```
 - Run the example project using SDK
    ```
    import mlflow

    mlflow.set_tracking_uri("<http://ip:port>")

    mlflow.run(".",
      experiment_name="My_Experiment",
      backend="oci-datascience",
      backend_config="oci-datascience-config.json"
    )
    ```
