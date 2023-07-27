=============
Release Notes
=============

1.0.2
-----
Release date: Jul 27, 2023

**New Features and Enhancements:**

* Changed the default authentication to the resource principal.


1.0.1
-----
Release date: Jun 15, 2023

**New Features and Enhancements:**

* Updated the ``README-development.md`` file for better clarity and ease of use.
* Improved the ``Dockerfile`` to provide the option of running the tracking server using a local ``oci-mlflow`` wheel.
* Refactored Object Storage (OS) plugin to leverage Oracle Cloud Infrastructure (OCI) `OS UploadManager <https://docs.oracle.com/en-us/iaas/tools/python/2.104.1/api/upload_manager.html>`__, enhancing the functionality and improving performance.

**Bug Fixes:**

* Fixed the issue with ``launch_mlflow.sh`` where the copyright information was added in the wrong place, resulting in an error when running ``launch_mlflow.sh``.