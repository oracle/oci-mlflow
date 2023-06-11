#!/bin/bash
# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/

export MLFLOW_TRACKING_URI=<http://ip:port>
mlflow run . --experiment-name sklearn/elastic_net --backend oci-datascience --backend-config ./oci-datascience-config.json
