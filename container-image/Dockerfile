# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

FROM ghcr.io/oracle/oraclelinux8-instantclient:21

RUN rm -rf /var/cache/yum/* && yum clean all && yum install -y gcc make patch vim iproute net-tools git && rm -rf /var/cache/yum/*
RUN curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh >> miniconda.sh
RUN bash ./miniconda.sh -b -p /miniconda; rm ./miniconda.sh;
ENV PATH="/miniconda/bin:$PATH"

USER root
# Create sync directory and expose as environment variable

ARG CONDA_ENV_FILE=environment.yaml
ARG CONDA_ENV_NAME=oci-mlflow
ARG MLFLOW_DIR=/etc/mlflow
ARG CONTAINER_ARTIFACT_DIR=container-image
ARG RND

COPY ${CONTAINER_ARTIFACT_DIR}/${CONDA_ENV_FILE} /opt/env.yaml
RUN conda install conda-forge::mamba && mamba env create -f /opt/env.yaml --name ${CONDA_ENV_NAME} && conda clean -afy
ENV PATH="/miniconda/envs/${CONDA_ENV_NAME}}/bin:$PATH"

RUN conda init bash && source ~/.bashrc && conda activate ${CONDA_ENV_NAME}

RUN mkdir ${MLFLOW_DIR}
COPY ${CONTAINER_ARTIFACT_DIR}/run/* ${MLFLOW_DIR}/
RUN chmod a+x ${MLFLOW_DIR}/launch_mlflow.sh

ENV MLFLOW_DIR=${MLFLOW_DIR}

EXPOSE 5000
HEALTHCHECK --interval=30s CMD curl -f -sI http://localhost:5000 || exit 1

RUN if [ -f ${MLFLOW_DIR}/oci_mlflow*.whl ]; then \
        local_whl=$(find ${MLFLOW_DIR} -name "*.whl" -exec basename {} \; | head -n 1 ); \
        source ~/.bashrc && conda activate ${CONDA_ENV_NAME} && pip install ${MLFLOW_DIR}/$local_whl; \
    fi

RUN echo "conda activate oci-mlflow">>/root/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

ENTRYPOINT [ "bash", "--login" , "-c"]
CMD ["python $MLFLOW_DIR/run.py"]
