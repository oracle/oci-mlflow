==============
Authentication
==============

MLflow now supports customizing auth for http request to MLflow tracking server. 

To inject OCI signer, perform the following steps:

* Install `oci-mlflow <https://pypi.org/project/oci-mlflow/>`__ sdk
* Set environment variable ``MLFLOW_TRACKING_AUTH`` as ``OCI_REQUEST_AUTH`` in code:

.. code-block:: python
    
    import os
    os.environ["MLFLOW_TRACKING_AUTH"] = "OCI_REQUEST_AUTH"

The oci-mlflow sdk will pick up the auth type from the environment variable and inject
the corresponding signer to all outgoing http request sent to MLflow tracking server.

Once the signer is present, the http request can be further authenticated and authorized.
Below is a simple example of using API Gateway and OCI Function to perform the authn/authz.

Example
-------

Prerequisites
~~~~~~~~~~~~~
* Install the lastest mlflow sdk
* Install the latest oci-mlflow sdk
* Add the following OCI policies

.. code-block:: shell

    Allow dynamic-group <dynamic_group> to manage api-gateway-family in compartment <compartment_name>
    Allow dynamic-group <dynamic_group> to manage functions-family in compartment <compartment_name>
    Allow any-user to use functions-family in compartment <compartment_name> where ALL {request.principal.type= 'ApiGateway'}
    Allow dynamic-group <dynamic_group> to {AUTHENTICATION_INSPECT,GROUP_MEMBERSHIP_INSPECT} in compartment <compartment_name>

Set up OCI Authorizer Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Git clone `oci-mlflow <https://github.com/oracle/oci-mlflow>`__ repository and navigate to ``authorizer`` folder

.. code-block:: shell

    git clone https://github.com/oracle/oci-mlflow.git
    cd oci-mlflow/authorizer

Build the OCI Authorizer Function image and push it to OCI Container Registry

.. code-block:: shell

    docker build -t <region>.ocir.io/<namespace>/<image>:<tag> -f Dockerfile .
    docker push <region>.ocir.io/<namespace>/<image>:<tag>

Create the OCI Function from the image just built following steps mentioned `here <https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingfunctions.htm#top>`__

In the OCI Function webpage, click the ``Configuration`` on the left and set
the group or dynamic group that have access to the tracking server via environment
variable ``GROUP_IDS`` in format ``ocid1.group.oc1..xxxx,ocid1.group.oc1..xxxx,ocid1.dynamicgroup.oc1..xxxx``.


Set up API Gateway
~~~~~~~~~~~~~~~~~~

Open OCI console and create/deploy API Gateway following steps mentioned `here <https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatinggateway.htm>`__

In the ``Authentication`` step while deploying API Gateway, click ``Single Authentication`` and select ``Authorizer Function``.

Choose the OCI Authorizer Function created in previous step and fill the ``Function arguments`` as follows.

.. list-table::
   :widths: 10 10 10
   :header-rows: 1

   * - Context table
     - Header name
     - Argument name
   * - request.header
     - accept-language
     - accept-language
   * - request.header
     - authorization
     - authorization
   * - request.header
     - host
     - host
   * - request.header
     - opc-request-id
     - opc-request-id
   * - request.header
     - date
     - x-date
   * - request.header
     - x-content-sha256
     - x-content-sha256
   * - request.header
     - content-length
     - content-length
   * - request.header
     - content-type
     - content-type
   * - request.header
     - path
     - (request-target)
   * - request.path
     - path
     - path

In the ``Routes`` step, set the ``Path`` as ``/api/2.0/mlflow/{path*}``. It's customizable to specify which rest api to authenticate or authorize.
This eample validates all outgoing http requests.

Choose ``HTTP`` in ``Backend Type`` and set the ``URL`` as ``<tracking_server_host>/api/2.0/mlflow/${request.path[path]}``. Replace the ``<tracking_server_host>`` with the actual tracking server host.


Set up MLflow Tracking URI and Environment Variable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set the API Gateway endpoint as the MLflow tracking server uri from previous step.

.. code-block:: python
    
    mlflow.set_tracking_uri("<api_gateway_endpoint>")

Set the environment variable ``MLFLOW_TRACKING_AUTH`` as ``OCI_REQUEST_AUTH``

.. code-block:: python
    
    import os
    os.environ["MLFLOW_TRACKING_AUTH"] = "OCI_REQUEST_AUTH"

Now all http request sent by mlflow sdk to tracking server will be injected with OCI
signer and authenticated/authorized by the Authorizer Function via API Gateway. Only
the authenticated oci credentials and authorized groups/dynamic groups can have access
to the tracking server. Once the validation succeeds, the request will be routed to
the backend tracking server.
