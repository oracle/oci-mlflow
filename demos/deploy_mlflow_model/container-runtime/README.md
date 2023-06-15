# Container based deployment

## Overview

This demo shows how to use containers for deploying models stored in MLflow registry.

1. Build Model

Run the `sklearn_elasticnet_wine <https://mflow.org>`__ in the project demos

2. Build Container image

To install conda dependencies on container image, copy over `conda.yaml` from the mlflow artifact and save it in the same folder as the `Dockefile.pyfunc`. The artifacts to build a container image is available in ``../container`` folder.

```
docker build -t {region}.ocir.io/<namesapce>/mlflow-model-runtime/sklearn:v1 -f Dockerfile.pyfunc .
```

### Push the container to OCIR

```
docker push {region}.ocir.io/<namespace>/mlflow-model-runtime/sklearn:v1
```


### Create Endpoint

Update ``elastic-net-deployment_container.yaml`` to reflect correct values for - 

* logId
* logGroupId
* logId
* projectId
* compartmentId
* image


```
MLFLOW_TRACKING_URI=<tracking uri> \
OCIFS_IAM_TYPE=api_key \
mlflow deployments \
    create --name elasticnet_test_deploy_container -m models:/ElasticnetWineModel/1 \
    -t oci-datascience \
    --config deploy-config-file=elastic-net-deployment-container.yaml
```

3. Invoke Prediction Endpoint

3.1 Using Python SDK

```
import requests
import oci
from oci.signer import Signer

body = {
    "dataframe_split": {
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
}



config = oci.config.from_file() 
auth = Signer(
  tenancy=config['tenancy'],
  user=config['user'],
  fingerprint=config['fingerprint'],
  private_key_file_location=config['key_file'],)

endpoint = 'https://modeldeployment.us-ashburn-1.oci.customer-oci.com/ocid1.datasciencemodeldeployment.oc1.iad..<unique_ID>/predict'


requests.post(endpoint, json=body, auth=auth, headers={}).json()

```

3.1 Using MLflow CLI

```

cat <<EOF> input.json
{
    "dataframe_split": {
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
          "alcohol"
      ],
      "data": [[7, 0.27, 0.36, 20.7, 0.045, 45, 170, 1.001, 3, 0.45, 8.8]],
      "index": [0]
    }
}
EOF

mlflow deployments predict --name ocid1.datasciencemodeldeployment.oc1.iad..<unique_ID> -t oci-datascience -I ./input.json
```
