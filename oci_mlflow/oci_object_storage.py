#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import os
from typing import List
from urllib.parse import urlparse

import fsspec
from ads.common import auth
from ads.common.oci_client import OCIClientFactory
from mlflow.entities import FileInfo
from mlflow.store.artifact.artifact_repo import ArtifactRepository
from mlflow.utils.file_utils import relative_path_to_artifact_path
from oci import object_storage
from oci.auth.signers import InstancePrincipalsDelegationTokenSigner
from ocifs import OCIFileSystem

from oci_mlflow import logger

OCI_SCHEME = "oci"
OCI_PREFIX = f"{OCI_SCHEME}://"
DEFAULT_DELEGATION_TOKEN_PATH = "/opt/spark/delegation-secrets/delegation.jwt"
DELEGATION_TOKEN_PATH = "DELEGATION_TOKEN_PATH"


def parse_os_uri(uri: str):
    """
    Parse an OCI object storage URI, returning tuple (bucket, namespace, path).

    Parameters
    ----------
    uri: str
        The OCI Object Storage URI.

    Returns
    -------
    Tuple
        The (bucket, ns, type)

    Raise
    -----
    Exception
        If provided URI is not an OCI OS bucket URI.
    """
    parsed = urlparse(uri)
    if parsed.scheme.lower() != OCI_SCHEME:
        raise Exception("Not an OCI object storage URI: %s" % uri)
    path = parsed.path

    if path.startswith("/"):
        path = path[1:]

    bucket, ns = parsed.netloc.split("@")

    return bucket, ns, path


def get_token_path():
    """
    Gets delegation token path.

    Return
    ------
    str
        The delegation token path.
    """
    token_path = (
        DEFAULT_DELEGATION_TOKEN_PATH
        if os.path.exists(DEFAULT_DELEGATION_TOKEN_PATH)
        else os.environ.get(DELEGATION_TOKEN_PATH)
    )
    return token_path


def get_delegation_token_signer(token_path: str):
    """
    Generate delegation token signer.

    Parameters
    ----------
    token_path: str
        The delegation token path.

    Return
    ------
    oci.auth.signers.InstancePrincipalsDelegationTokenSigner
        The delegation token signer.

    """
    with open(token_path) as fd:
        delegation_token = fd.read()
    signer = InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)
    return signer


def get_signer(token_path: str = None):
    """
    Generate default_signer. If running in Data Flow, use InstancePrincipalsDelegationTokenSigner.
    If running locally, use default signer.

    Parameters
    ----------
    token_path: str
        Defaults to None. The delegation token path.

    Return
    ------
    dict
        Contains keys - config, signer and client_kwargs.

        - The config contains the config loaded from the configuration loaded from the default location if the default
          auth mode is API keys, otherwise it is empty dictionary.
        - The signer contains the signer object created from default auth mode.
        - client_kwargs contains the `client_kwargs` that was passed in as input parameter.

    """
    if token_path:
        auth.set_auth(
            signer_callable=get_delegation_token_signer,
            signer_kwargs={"token_path": token_path},
        )
    return auth.default_signer()


class ArtifactUploader:
    """
    The class helper to upload model artifacts.

    Attributes
    ----------
    upload_manager: UploadManager
        The uploadManager simplifies interaction with the Object Storage service.
    """

    def __init__(self):
        """Initializes `ArtifactUploader` instance."""
        self.upload_manager = object_storage.UploadManager(
            OCIClientFactory(**get_signer(token_path=get_token_path())).object_storage
        )

    def upload(self, file_path: str, dst_path: str):
        """Uploads model artifacts.

        Parameters
        ----------
        file_path: str
            The source file path.
        dst_path: str
            The destination path.
        """
        bucket_name, namespace_name, object_name = parse_os_uri(dst_path)
        logger.debug(f"{bucket_name=}, {namespace_name=}, {object_name=}")
        response = self.upload_manager.upload_file(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=file_path,
        )
        logger.debug(response)


class OCIObjectStorageArtifactRepository(ArtifactRepository):
    """MLFlow Plugin implementation for storing artifacts to OCI Object Storage."""

    def _download_file(self, remote_file_path, local_path):
        if not remote_file_path.startswith(self.artifact_uri):
            full_path = os.path.join(self.artifact_uri, remote_file_path)
        else:
            full_path = remote_file_path
        fs: OCIFileSystem = self.get_fs()
        logger.info(f"{full_path}, {remote_file_path}")
        fs.download(full_path, str(local_path))

    def log_artifact(self, local_file: str, artifact_path: str = None):
        """
        Logs a local file as an artifact, optionally taking an ``artifact_path`` to place it in
        within the run's artifacts. Run artifacts can be organized into directories, so you can
        place the artifact in a directory this way.

        Parameters
        ----------
        local_file:str
            Path to artifact to log.
        artifact_path:str
            Directory within the run's artifact directory in which to log the artifact.
        """
        # Since the object storage path should contain "/", the code below needs to use concatenation "+" instead of 
        # os.path.join(). The latter can introduce "\" in Windows which can't be recognized by object storage as a valid prefix. 
        # `artifact_path` must not be space character like " " or "   ".
        if isinstance(artifact_path, str) and artifact_path.isspace():
            raise ValueError("`artifact_path` must not be whitespace string.")
        artifact_path = artifact_path.rstrip("/") + "/" if artifact_path else ""
        dest_path = self.artifact_uri.rstrip("/") + "/" + artifact_path + os.path.basename(local_file)
        ArtifactUploader().upload(local_file, dest_path)

    def log_artifacts(self, local_dir: str, artifact_path: str = None):
        """
        Logs the files in the specified local directory as artifacts, optionally taking
        an ``artifact_path`` to place them in within the run's artifacts.

        Parameters
        ----------
        local_dir:str
            Directory of local artifacts to log.
        artifact_path:str
            Directory within the run's artifact directory in which to log the artifacts.
        """
        artifact_uploader = ArtifactUploader()
        # Since the object storage path should contain "/", the code below needs to use concatenation "+" instead of 
        # os.path.join(). The latter can introduce "\" in Windows which can't be recognized by object storage as a valid prefix. 
        # `artifact_path` must not be space character like " " or "   ".
        if isinstance(artifact_path, str) and artifact_path.isspace():
            raise ValueError("`artifact_path` must not be whitespace string.")
        artifact_path = artifact_path.rstrip("/") + "/" if artifact_path else ""
        dest_path = self.artifact_uri.rstrip("/") + "/" + artifact_path
        local_dir = os.path.abspath(local_dir)

        for root, _, filenames in os.walk(local_dir):
            upload_path = dest_path
            if root != local_dir:
                rel_path = os.path.relpath(root, local_dir)
                rel_path = relative_path_to_artifact_path(rel_path)
                upload_path = dest_path + rel_path
            for f in filenames:
                artifact_uploader.upload(
                    file_path=os.path.join(root, f),
                    dst_path=upload_path + f
                )

    def get_fs(self):
        """
        Gets fssepc filesystem based on the uri scheme.
        """
        self.fs = fsspec.filesystem(
            urlparse(self.artifact_uri).scheme,
            **get_signer(token_path=get_token_path()),
        )  # FileSystem class corresponding to the URI scheme.

        return self.fs

    def list_artifacts(self, path: str = "") -> List[FileInfo]:
        """
        Return all the artifacts for this run_id directly under path. If path is a file, returns
        an empty list. Will error if path is neither a file nor directory.

        Parameters
        ----------
        path:str
            Relative source path that contains desired artifacts

        Returns
        -------
        List[FileInfo]
            List of artifacts as FileInfo listed directly under path.
        """
        result = []
        dest_path = self.artifact_uri
        if path:
            dest_path = os.path.join(dest_path, path)

        logger.debug(f"{path=}, {self.artifact_uri=}, {dest_path=}")

        fs = self.get_fs()
        files = (
            os.path.relpath(f"{OCI_PREFIX}{f}", self.artifact_uri)
            for f in fs.glob(f"{dest_path}/*")
        )

        for file in files:
            file_isdir = fs.isdir(os.path.join(self.artifact_uri, file))
            size = 0
            if not file_isdir:
                size = fs.info(os.path.join(self.artifact_uri, file)).get("size", 0)
            result.append(FileInfo(file, file_isdir, size))

        logger.debug(f"{result=}")

        result.sort(key=lambda f: f.path)
        return result

    def delete_artifacts(self, artifact_path: str = None):
        """
        Delete the artifacts at the specified location.
        Supports the deletion of a single file or of a directory. Deletion of a directory
        is recursive.

        Parameters
        ----------
        artifact_path: str
            Path of the artifact to delete.
        """
        dest_path = self.artifact_uri
        if artifact_path:
            dest_path = os.path.join(self.artifact_uri, artifact_path)
        fs = self.get_fs()
        files = fs.ls(dest_path, refresh=True)
        for to_delete_obj in files:
            fs.delete(to_delete_obj)
