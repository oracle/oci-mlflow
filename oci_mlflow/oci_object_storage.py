#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import os
from urllib.parse import urlparse

import fsspec
from mlflow.entities import FileInfo
from mlflow.store.artifact.artifact_repo import ArtifactRepository
from mlflow.utils.file_utils import relative_path_to_artifact_path
from ocifs import OCIFileSystem

from oci_mlflow import logger

OCI_PREFIX = "oci://"


class OCIObjectStorageArtifactRepository(ArtifactRepository):
    """
    MLFlow Plugin implementation for storing artifacts to OCI Object Storage
    """

    @staticmethod
    def parse_os_uri(uri):
        """Parse an OCI object storage URI, returning (bucket, namespace, path)"""
        parsed = urlparse(uri)
        if parsed.scheme != "oci":
            raise Exception("Not an OCI object storage URI: %s" % uri)
        path = parsed.path
        if path.startswith("/"):
            path = path[1:]
        bucket, ns = parsed.netloc.split("@")
        return bucket, ns, path

    def _upload_file(self, local_file, dest_path):
        with open(local_file, "rb") as data:
            with fsspec.open(dest_path, "wb") as outfile:
                outfile.write(data.read())

    def _download_file(self, remote_file_path, local_path):
        if not remote_file_path.startswith(self.artifact_uri):
            full_path = os.path.join(self.artifact_uri, remote_file_path)
        else:
            full_path = remote_file_path
        fs: OCIFileSystem = self.get_fs()
        logger.info(f"{full_path}, {remote_file_path}")
        fs.download(full_path, local_path)

    def log_artifact(self, local_file, artifact_path=None):
        if artifact_path:
            dest_path = os.path.join(self.artifact_uri, artifact_path)
        else:
            dest_path = self.artifact_uri
        dest_path = os.path.join(dest_path, os.path.basename(local_file))
        self._upload_file(local_file, dest_path)

    def log_artifacts(self, local_dir, artifact_path=None):
        if artifact_path:
            dest_path = os.path.join(self.artifact_uri, artifact_path)
        else:
            dest_path = artifact_path
        local_dir = os.path.abspath(local_dir)
        for (root, _, filenames) in os.walk(local_dir):
            upload_path = dest_path
            if root != local_dir:
                rel_path = os.path.relpath(root, local_dir)
                rel_path = relative_path_to_artifact_path(rel_path)
                upload_path = os.path.join(dest_path, rel_path)
            for f in filenames:
                self._upload_file(
                    local_file=os.path.join(root, f),
                    dest_path=os.path.join(upload_path, f),
                )

    def get_fs(self):
        """
        Get fssepc filesystem based on the uri scheme
        """
        self.fs = fsspec.filesystem(
            urlparse(self.artifact_uri).scheme
        )  # FileSystem class corresponding to the URI scheme.

        return self.fs

    def list_artifacts(self, path: str = ""):
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

    def delete_artifacts(self, artifact_path=None):
        dest_path = self.artifact_uri
        if artifact_path:
            dest_path = os.path.join(self.artifact_uri, artifact_path)
        fs = self.get_fs()
        files = fs.ls(dest_path, refresh=True)
        for to_delete_obj in files:
            fs.delete(to_delete_obj)
