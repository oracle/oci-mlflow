=====================
Setup Tracking server
=====================

`MLflow tracking
server <https://mlflow.org/docs/latest/tracking.html>`__ provides
logistics for tracking machine learning experiments. The server
provides APIs for storing and retrieving model performance metrics,
models, environment details, etc. The UI also provides dashboarding
capabilities to compare experiment runs.

The easiest way to setup the tracking server is by deploying the MLflow
container image provided by OCI. Refer to
`this <https://mlflow.org/docs/latest/tracking.html#how-runs-and-artifacts-are-recorded>`__
page to understand various deployment options for MLflow. You could
choose from any of the deployment options.

Build ``oci-mlflow`` Container Image
------------------------------------

.. admonition:: Prerequisites
   :class: note

   1. Container registry URL. Pick one from `here <https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryprerequisites.htm#regional-availability>`__ that applies to your tenancy
   2. Docker build tools
   3. Become familiar with the `Oracle Container Registry <https://docs.oracle.com/en-us/iaas/Content/Registry/home.htm>`__

Steps to build image
~~~~~~~~~~~~~~~~~~~~

1. Pull the `oci-mlflow <https://github.com/oracle/oci-mlflow>`__ repository from the GitHub. Go to the ``container-image`` folder.
2. Build the image by running following command -

   ::

      # The image-name should be in the pattern - {region}.ocir.io/{tenancy}/oci-mlflow:{tag}
      # Eg. docker build -t iad.ocir.io/mytenancy/oci-mlflow:latest --network host -f container-image/Dockerfile .
      docker build -t {region}.ocir.io/{tenancy}/oci-mlflow:{tag} --network host -f container-image/Dockerfile .

   To publish an image to the Oracle Container Registry, it can be beneficial to follow the format: ``{region}.ocir.io/{tenancy}/oci-mlflow:{tag}``. This format provides a structured approach for naming the image. However, it is not mandatory to adhere strictly to this format. You have the flexibility to choose any name for the image and then use the ``docker tag`` command to create an alias for the image. This alias can then be used to publish the image to the Oracle Container Registry (OCR). If you need more information about OCR, you can refer to the `Oracle Container Registry documentation <https://docs.oracle.com/en-us/iaas/Content/Registry/home.htm>`__.

Setup ``oci-mlflow`` Container Image
------------------------------------
In the examples below we use ``--network host`` option to share container's network namespace with the host machine. Alternatively the ``-p 5000:5000`` can be used to expose the port for the container.

Run locally on laptop -
~~~~~~~~~~~~~~~~~~~~~~~

The default options will assume you want to store the artifacts in your
local file system and use ``sqlite`` for recording experiments data.

   ::

      docker run --rm \
      --name oci-mlflow \
      --network host \
      -e MLFLOW_HOST=0.0.0.0 \
      -e MLFLOW_GUNICORN_OPTS='--log-level debug' \
      {region}.ocir.io/{tenancy}/oci-mlflow:{tag}


Check the MLflow UI at ``http://localhost:5000``

Auth Configuration
~~~~~~~~~~~~~~~~~~

To interact with OCI resources, the container needs to authenticate with
OCI service. To configure the authentication mechanism, use environment
variable ``OCIFS_IAM_TYPE``. The authentication mechanism could be one
of the following

1. ``api_key``. To setup ``api_key``, mount the
directory where oci keys are stored to ``/root/.oci`` path. **Note**:
The reference to the path to private key inside the ``oci`` ``config``
file should be such that it is valid inside the container. Instead of
hard coding your home folder, you should use ``~`` so that your config
file is valid both inside and outside the container.

   ::

      docker run --rm \
      --name oci-mlflow \
      --network host
      -e MLFLOW_HOST=0.0.0.0 \
      -e MLFLOW_GUNICORN_OPTS='--log-level debug' \
      -e OCIFS_IAM_TYPE=api_key \
      -v ~/.oci:/root/.oci \
      {region}.ocir.io/{tenancy}/oci-mlflow:{tag}

2. ``resource_principal``. This option is valid only if you are running
the container on `container instance <https://www.oracle.com/cloud/cloud-native/container-instances/>`__

   ::

      docker run --rm \
      --name oci-mlflow \
      --network host \
      -e MLFLOW_HOST=0.0.0.0 \
      -e MLFLOW_GUNICORN_OPTS='--log-level debug' \
      -e OCIFS_IAM_TYPE=resource_principal \
      {region}.ocir.io/{tenancy}/oci-mlflow:{tag}

3. ``instance_principal``. This option is valid only if you are running
the container on `compute instance <https://docs.oracle.com/en-us/iaas/Content/Compute/Concepts/computeoverview.htm>`__

   ::

      docker run --rm \
      --name oci-mlflow \
      --network host \
      -e MLFLOW_HOST=0.0.0.0 \
      -e MLFLOW_GUNICORN_OPTS='--log-level debug' \
      -e OCIFS_IAM_TYPE=instance_principal \
      {region}.ocir.io/{tenancy}/oci-mlflow:{tag}

Setup object storage bucket to save artifacts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default setup will save model artifacts in local filesystem. To
setup object storage, set environment variable - ``MLFLOW_DEFAULT_ARTIFACT_ROOT`` and ``MLFLOW_ARTIFACTS_DESTINATION``
to object storage path using following format -
``oci://<bucket>@<namespace>/`` .

::

   docker run --rm \
   --name oci-mlflow \
   --network host \
   -e MLFLOW_HOST=0.0.0.0 \
   -e MLFLOW_GUNICORN_OPTS='--log-level debug' \
   -e OCIFS_IAM_TYPE=api_key \
   -e MLFLOW_DEFAULT_ARTIFACT_ROOT=oci://bucket@namespace/prefix/ \
   -e MLFLOW_ARTIFACTS_DESTINATION=oci://bucket@namespace/prefix/  \
   -e MLFLOW_SERVE_ARTIFACTS=1 \
   -v ~/.oci:/root/.oci \
   {region}.ocir.io/{tenancy}/oci-mlflow:{tag}

.. admonition:: See also
   :class: note

   Refer `Environment Variables section <https://mlflow.org/docs/latest/cli.html#mlflow-server>`__ for additional configuration.

.. _mysql-setup:

Setup MySQL Database to save experiments data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. admonition:: Prerequisites
   :class: note

   -  Provision `MySQL Database <https://www.oracle.com/mysql/>`__ on OCI
   -  Create a new database named ``mlflow`` in the mysql instance. All the required tables and views will be automatically created by the MLflow.
   -  Optionally, for secure access to credentials, save the MySQL credentials to
      `OCI
      Vault <https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm>`__
      using `MySQLDBSecretKeeper <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/secrets/mysql.html>`__

Set environment variable ``BACKEND_PROVIDER=mysql`` to configure MLflow
tracking server to use MySQL. The database connection details can be
either provided directly using environment variables or through
``vault``. To configure the credentials directly, use environment variable ``MLFLOW_BACKEND_STORE_URI`` with mysql URI as the value. The URI format is - ``mysql+mysqlconnector://{username}:{password}@{host}:{db_port}/{db_name}``

::

   docker run --rm \
   --name oci-mlflow \
   --network host \
   -e MLFLOW_HOST=0.0.0.0 \
   -e MLFLOW_GUNICORN_OPTS='--log-level debug' \
   -e OCIFS_IAM_TYPE=api_key \
   -e MLFLOW_DEFAULT_ARTIFACT_ROOT=oci://bucket@namespace/prefix/ \
   -e MLFLOW_ARTIFACTS_DESTINATION=oci://bucket@namespace/prefix/ \
   -e BACKEND_PROVIDER=mysql \
   -e MLFLOW_BACKEND_STORE_URI=mysql+mysqlconnector://{username}:{password}@{host}:{db_port}/{db_name} \
   -e MLFLOW_SERVE_ARTIFACTS=1 \
   -v ~/.oci:/root/.oci \
   {region}.ocir.io/{tenancy}/oci-mlflow:{tag}

To setup the credentials using ``Vault``, save the credentials to
``Vault``, using ``oracle-ads``. Check ``oracle-ads``
`documentation <https://accelerated-data-science.readthedocs.io/en/latest/user_guide/secrets/mysql.html#id1>`__
to see how to save MySQL credentials in the right format. Once the
credentials are saved, use the ``vaultsecret`` OCID to configure the
container.
To configure the ``vaultsecret`` OCID use environment variable - ``DB_SECRET_OCID``

::

   docker run --rm \
   --name oci-mlflow \
   --network host \
   -e MLFLOW_HOST=0.0.0.0 \
   -e MLFLOW_GUNICORN_OPTS='--log-level debug' \
   -e OCIFS_IAM_TYPE=api_key \
   -e MLFLOW_DEFAULT_ARTIFACT_ROOT=oci://bucket@namespace/prefix/ \
   -e MLFLOW_ARTIFACTS_DESTINATION=oci://bucket@namespace/prefix/ \
   -e BACKEND_PROVIDER=mysql \
   -e DB_SECRET_OCID=ocid1.vaultsecret.oc1.iad..<unique_ID> \
   -e MLFLOW_SERVE_ARTIFACTS=1 \
   -v ~/.oci:/root/.oci \
   {region}.ocir.io/{tenancy}/oci-mlflow:{tag}

Deploying on OCI using Container Instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Container Instance <https://cloud.oracle.com/compute/container-instances>`__
enables you to easily run containers without having to manage a compute
directly. Container instance offers ``resource_principal`` based
authentication which makes setting up access to the ``object storage``
bucket and ``Vault`` easy via polices. Learn more about container
instance policy
`here <https://docs.oracle.com/en-us/iaas/Content/container-instances/permissions/policy-reference.htm>`__

.. admonition:: Prerequisites
   :class: note

   1. Build the container image for ``oci-mlflow``
   2. Push the docker image to ocir -
      ::

         docker push {region}.ocir.io/{tenancy}/oci-mlflow:{tag}

Policies
--------

Dynamic Group
~~~~~~~~~~~~~

Container instances are recognized using
``resource.type='computecontainerinstance'``. Create a dynamic group which identifies ``computecontainerinstance``.

Access Policies
~~~~~~~~~~~~~~~

-  Object storage Access:

   ``Allow dynamic-group <your dynamic group> to manage objects in compartment <your_compartment_name> where all {target.bucket.name=<your_bucket_name>}``

-  Vault:

   ``Allow dynamic-group container-instance-group to use secret-family in compartment <your_compartment_name>``

Security
--------

The tracking server by default does not authenticate the user. If you
are using public IP use a reverse proxy to authenticate and authorize
incoming traffic.

Enabling Ingress to Tracking server Port
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default port of the tracking server is ``5000``. By default all ingress traffic to the subnet is blocked. To enable ingress to port ``5000`` or any port that you choose for your tracking server, you need to attach `security list <https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm>`__ to your subnet which contains ingress rule to allow TCP traffic to port ``5000``.

Here is a sample ingress rule setting for allowing traffic from any IP address to port ``5000``. You can restrict the incoming traffic from specific range of IPs by providing appropriate CIDR block in ``Source`` -

+----------------------+----------+
|Source:               | 0.0.0.0/0|
+----------------------+----------+
|IP Protocol           | TCP      |
+----------------------+----------+
|Source Port Range     | All      |
+----------------------+----------+
|Destination Port Range| 5000     |
+----------------------+----------+


Environment Variables
---------------------

Following are mandatory Environment variables -

+---------------------------+---------+-------------------------+
| Environment Variable name | Value   | Description             |
+===========================+=========+=========================+
| MLFLOW_HOST               | 0.0.0.0 | Bind to all IPs on host |
+---------------------------+---------+-------------------------+

Following are recommended environment variables, but optional

+------------------------------+------------------------------------------+-----------------------------------------------------------------+
| Environment Variable name    | Value                                    | Description                                                     |
+==============================+==========================================+=================================================================+
| MLFLOW_ARTIFACTS_DESTINATION | oci://bucket@namespace/prefix            | Object storage location to store artifacts                      |
+------------------------------+------------------------------------------+-----------------------------------------------------------------+
| MLFLOW_DEFAULT_ARTIFACT_ROOT | Set same as MLFLOW_ARTIFACTS_DESTINATION |                                                                 |
+------------------------------+------------------------------------------+-----------------------------------------------------------------+
| MLFLOW_SERVE_ARTIFACTS       | 1                                        | Configure Tracking server to serve artifacts                    |
+------------------------------+------------------------------------------+-----------------------------------------------------------------+
| MLFLOW_GUNICORN_OPTS         | --log-level debug                        | To see debug logs                                               |
+------------------------------+------------------------------------------+-----------------------------------------------------------------+
| MLFLOW_WORKERS               | equal to cores                           | Default is 4, you can adjust this as per the resource allocated |
+------------------------------+------------------------------------------+-----------------------------------------------------------------+

For setting up database, use the environment variables listed :ref:`mysql-setup`
