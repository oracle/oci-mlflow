# Development
The target audience for this README is developers wanting to contribute to `OCI MLflow` plugins. If you want to use the OCI MLflow plugins with your own programs, see `README.md`.

## Setting Up Dependencies

```
python3 -m pip install -r dev-requirements.txt
```

## Setting Up Tracking Server

Create a file called `.env` in the root folder of the project with following contents -

```
# Defaults to resource_principal if not provided
OCIFS_IAM_TYPE=api_key

# Artifacts location. Can be local folder or OCI Object Storage bucket
MLFLOW_ARTIFACTS_DESTINATION=oci://bucket@namespace/
MLFLOW_DEFAULT_ARTIFACT_ROOT=oci://bucket@namespace/

# Backend provider. Default is sqllite
BACKEND_PROVIDER=sqllite

# ------MySQL-----------------------
# BACKEND_PROVIDER=mysql

# The database credentials can be stored in the Vault service, or they can be provided in the config. See more details how to save the credentials to the Vault - https://accelerated-data-science.readthedocs.io/en/latest/user_guide/secrets/mysql.html

# DB_SECRET_OCID=ocid1.vaultsecret.oc1.iad..<unique_ID>
# DBHOST=<host ip>
# DBUSERNAME=<db username>
# DBPASSWORD=<password>
# ------------------------------------

MLFLOW_SERVE_ARTIFACTS=1
MLFLOW_GUNICORN_OPTS=--log-level debug
MLFLOW_WORKERS=4
MLFLOW_HOST=0.0.0.0
```

### Building And Running Tracking Server

To build an `oci-mlflow` container image run -

```
make build-image
```

To build and launch tracking server run -

```
make launch
```

To build `oci-mlflow` wheel file and then rebuild and launch the container image, run -

```
make wheel launch
```

To build and start a shell prompt within `oci-mlflow` container image, run -

```
make launch-shell
```


# Running Tests
The SDK uses pytest as its test framework. To run tests use:

```
python3 -m pytest tests/*
```

# Generating Documentation
Sphinx is used for documentation. You can generate HTML locally with the following:

```
python3 -m pip install -r dev-requirements.txt
cd docs
make html
```

# Generating the wheel
The OCI MLflow plugins are packaged as a wheel. To generate the wheel, you can run:

```
make build
```

This wheel can then be installed using pip.
