#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import ads
import logging
import os
import sys
import subprocess
import shlex

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

BACKEND_PROVIDER = os.environ.get("BACKEND_PROVIDER", "sqlite")
MYSQL = "mysql"
SQLITE = "sqlite"
OBJECT_STORAGE = "object_storage"
DEFAULT_DB_NAME = "mlflow"
ARTIFACT_STORE_URI = "ARTIFACT_STORE_URI"
EXTRA_MLFLOW_OPTIONS = "EXTRA_MLFLOW_OPTIONS"
MLFLOW_LAUNCH_SCRIPT = "/etc/mlflow/launch_mlflow.sh"
DB_SECRET_OCID = "DB_SECRET_OCID"
PATCH_SCRIPT_PATH = "/etc/mlflow/patches"


# Default authentication is resource_principal. To switch to other authentications forms such as `api_key` or `instance_principal`
# set the environment variable - `OCIFS_IAM_TYPE`

AUTH_TYPE = os.environ.get("OCIFS_IAM_TYPE", "resource_principal")


class BackendStore:
    def uri():
        pass


class MySQLBackendStore(BackendStore):
    DEFAULT_PORT = "3306"

    def uri():
        """
        Fetch credentials from vault using secret ocid. This requires the credentials to be saved in vault using oracle-ads provided API.
        More information - https://accelerated-data-science.readthedocs.io/en/latest/user_guide/secrets/mysql.html

        If vault ocid is not supplied, retrieve db credentials from the environment variable.
        """
        if os.environ.get(DB_SECRET_OCID):
            from ads.secrets.mysqldb import MySQLDBSecretKeeper

            secret_ocid = os.environ[DB_SECRET_OCID]
            logger.info(
                f"Found environment variable {DB_SECRET_OCID}. Retrieving secret using auth type: {AUTH_TYPE}"
            )

            ads.set_auth(AUTH_TYPE)

            mysqldb_secret = MySQLDBSecretKeeper.load_secret(secret_ocid).to_dict()
            username = mysqldb_secret["user_name"]
            password = mysqldb_secret["password"]
            host = mysqldb_secret["host"]
            db_port = mysqldb_secret.get("port", MySQLBackendStore.DEFAULT_PORT)
            db_name = mysqldb_secret.get(
                "database"
            )  # if database was not saved in the secret, the value for 'database' will be None
            if db_name is None:
                db_name = DEFAULT_DB_NAME
        else:
            username = os.environ.get("DBUSERNAME")
            password = os.environ.get("DBPASSWORD")
            host = os.environ.get("DBHOST")
            db_name = os.environ.get("DBNAME", DEFAULT_DB_NAME)
            db_port = os.environ.get("DBPORT", MySQLBackendStore.DEFAULT_PORT)

        return (
            f"mysql+mysqlconnector://{username}:{password}@{host}:{db_port}/{db_name}"
        )


class SQLiteBackendStore(BackendStore):
    def uri():
        """
        Reference:
        ----------

        https://mlflow.org/docs/latest/tracking.html#scenario-3-mlflow-on-localhost-with-tracking-server

        """
        return "sqlite:///mydb.sqlite"


class BackendStoreFactory:
    providers = {MYSQL: MySQLBackendStore, SQLITE: SQLiteBackendStore}

    @classmethod
    def handler(cls, name):
        return cls.providers.get(name)


def generate_backend_store_uri(provider):
    return BackendStoreFactory.handler(provider).uri()


def configure_mlflow_environment():
    mlflow_options = {}
    if not os.environ.get("MLFLOW_BACKEND_STORE_URI"):
        backend_store_uri = generate_backend_store_uri(BACKEND_PROVIDER)
        mlflow_options = {"backend-store-uri": backend_store_uri}

    mlflow_cmd_option = " ".join([f"--{k} {mlflow_options[k]}" for k in mlflow_options])
    return mlflow_cmd_option


def launch_mlflow():
    try:
        mlflow_cmd_option = configure_mlflow_environment()
    except Exception as e:
        logger.error(e)
        raise Exception("Failed to create MLFlow configuration")

    # shlex.split can cause issues for "--gunicorn-opts".
    # It is better to pass extra args through environment variables.
    # More info - https://mlflow.org/docs/latest/cli.html#mlflow-server
    cmd_split = shlex.split(mlflow_cmd_option)
    subprocess.run(
        [MLFLOW_LAUNCH_SCRIPT] + cmd_split,  # capture_output=True
    )


if __name__ == "__main__":
    launch_mlflow()
