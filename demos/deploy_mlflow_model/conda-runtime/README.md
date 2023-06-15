# Conda Environment based Deployment

This example demonstrates how to use a conda pack based on the conda.yaml in the MLflow model to deploy a model. MLflow model consists of conda.yaml which captures the required dependencies for running the model.

## Create a model and register

1. Build Model

Run the `sklearn_elasticnet_wine <https://mflow.org>`__ in the project demos

2. Deploy Model

There are two example specification in the folder -
* ``elastic-net-deployment_build_conda.yaml``: This will be build conda environment and export it as conda pack, uploads to object storage and deploy
* ``elastic-net-deployment_prebuilt_conda.yaml``: This will use the conda pack that is already saved in the object storage

Update the yaml file to reflect correct values for -

* logId
* logGroupId
* projectId
* compartmentId
* uri with the right bucket name and namespace



```
MLFLOW_TRACKING_URI=<tracking uri> \
OCIFS_IAM_TYPE=api_key \
mlflow deployments \
    create --name elasticnet_test_deploy -m models:/ElasticnetWineModel/1 \
    -t oci-datascience \
    --config deploy-config-file=elastic-net-deployment_build_conda.yaml

```

1. Invoke Prediction Endpoint

```
import requests
import oci
from oci.signer import Signer

body = {
    "columns": [
        "fixed acidity",
        "volatile acidity",
        "citric acid",
        "residual sugar",
        "chlorides",
        "free sulfur dioxide",
        "total sulfur dioxide",
        "density",
        "pH",
        "sulphates",
        "alcohol",
    ],
    "data": [[7, 0.27, 0.36, 20.7, 0.045, 45, 170, 1.001, 3, 0.45, 8.8]],
    "index": [0],
}



config = oci.config.from_file()
auth = Signer(
  tenancy=config['tenancy'],
  user=config['user'],
  fingerprint=config['fingerprint'],
  private_key_file_location=config['key_file'],)

endpoint = 'https://modeldeployment.us-ashburn-1.oci.customer-oci.com/ocid1.datasciencemodeldeployment.oc1.iad.<unique_ID>/predict'


requests.post(endpoint, json=body, auth=auth, headers={}).json()
```
