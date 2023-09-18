#!/bin/bash --login
# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/

set -m -e -o pipefail

conda activate oci-mlflow

echo "========== MLflow server is launchng... =========="

mlflow server $@

echo "========== MLflow server is shutting down... =========="

exit $LastExitCode
