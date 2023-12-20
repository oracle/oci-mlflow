#!/usr/bin/env python
# -*- coding: utf-8; -*-

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import pytest
from mlflow.entities import FileInfo

from oci_mlflow import oci_object_storage
from oci_mlflow.oci_object_storage import (
    ArtifactUploader,
    OCIObjectStorageArtifactRepository,
    get_token_path,
    get_signer,
    DEFAULT_DELEGATION_TOKEN_PATH,
)
from oci import object_storage


class DataObject:
    def __init__(self, name, size):
        self.name = name
        self.size = size


class TestOCIObjectStorageArtifactRepository:
    def setup_class(cls):
        cls.curr_dir = os.path.dirname(os.path.abspath(__file__))
        oci_object_storage.OCI_PREFIX = ""

    @classmethod
    def teardown_class(cls):
        oci_object_storage.OCI_PREFIX = "oci://"

    @pytest.fixture()
    def oci_artifact_repo(self):
        return OCIObjectStorageArtifactRepository(
            artifact_uri="oci://my-bucket@my-namespace/my-artifact-path"
        )

    @pytest.fixture
    def mock_fsspec_open(self):
        with patch("fsspec.open") as mock_open:
            yield mock_open

    def test_parse_os_uri(self, oci_artifact_repo):
        bucket, namespace, path = oci_object_storage.parse_os_uri(
            "oci://my-bucket@my-namespace/my-artifact-path"
        )
        assert bucket == "my-bucket"
        assert namespace == "my-namespace"
        assert path == "my-artifact-path"

    def test_parse_os_uri_with_invalid_scheme(self, oci_artifact_repo):
        with pytest.raises(Exception):
            oci_object_storage.parse_os_uri("s3://my-bucket/my-artifact-path")

    def test_download_file(self, oci_artifact_repo):
        mock_fs = MagicMock()
        mock_fs.download.return_value = None
        oci_artifact_repo.get_fs = MagicMock(return_value=mock_fs)
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = os.path.join(tmp_dir, "my_file.txt")
            remote_path = "my/remote/path/my_file.txt"

            oci_artifact_repo._download_file(
                remote_file_path=remote_path, local_path=local_path
            )

            mock_fs.download.assert_called_once_with(
                "oci://my-bucket@my-namespace/my-artifact-path/my/remote/path/my_file.txt",
                local_path,
            )

    @patch.object(ArtifactUploader, "upload")
    def test_log_artifact(self, mock_upload_file, oci_artifact_repo):
        local_file = "test_files/test.txt"
        artifact_path = "logs"
        oci_artifact_repo.log_artifact(local_file, artifact_path)
        expected_dest_path = (
            "oci://my-bucket@my-namespace/my-artifact-path/logs/test.txt"
        )
        mock_upload_file.assert_called_once_with(local_file, expected_dest_path)

    @patch.object(ArtifactUploader, "upload")
    def test_log_artifact_with_empty_path(self, mock_upload_file, oci_artifact_repo):
        local_file = "test_files/test.txt"
        artifact_path = ""
        oci_artifact_repo.log_artifact(local_file, artifact_path)
        expected_dest_path = (
            "oci://my-bucket@my-namespace/my-artifact-path/test.txt"
        )
        mock_upload_file.assert_called_once_with(local_file, expected_dest_path)

    def test_log_artifact_with_whitespace(self, oci_artifact_repo):
        local_file = "test_files/test.txt"
        artifact_path = "  "
        with pytest.raises(
            ValueError,
            match="`artifact_path` must not be whitespace string."
        ):
            oci_artifact_repo.log_artifact(local_file, artifact_path)

    @patch.object(ArtifactUploader, "upload")
    def test_log_artifact_with_none(self, mock_upload_file, oci_artifact_repo):
        local_file = "test_files/test.txt"
        artifact_path = None
        oci_artifact_repo.log_artifact(local_file, artifact_path)
        expected_dest_path = (
            "oci://my-bucket@my-namespace/my-artifact-path/test.txt"
        )
        mock_upload_file.assert_called_once_with(local_file, expected_dest_path)

    @patch.object(ArtifactUploader, "upload")
    def test_log_artifact_with_slash_ending_path(self, mock_upload_file, oci_artifact_repo):
        local_file = "test_files/test.txt"
        artifact_path = "logs/"
        oci_artifact_repo.log_artifact(local_file, artifact_path)
        expected_dest_path = (
            "oci://my-bucket@my-namespace/my-artifact-path/logs/test.txt"
        )
        mock_upload_file.assert_called_once_with(local_file, expected_dest_path)

    @patch.object(ArtifactUploader, "upload")
    def test_log_artifacts(self, mock_upload_file, oci_artifact_repo):
        local_dir = os.path.join(self.curr_dir, "test_files")
        dest_path = "path/to/dest"
        oci_artifact_repo.log_artifacts(local_dir, dest_path)
        mock_upload_file.assert_called()

    @patch.object(OCIObjectStorageArtifactRepository, "get_fs")
    def test_delete_artifacts(self, mock_get_fs, oci_artifact_repo):
        mock_fs = Mock()
        mock_get_fs.return_value = mock_fs
        mock_fs.ls.return_value = ["test/file1", "test/file2", "test/folder/"]
        oci_artifact_repo.delete_artifacts("test")
        mock_fs.ls.assert_called_once_with(
            "oci://my-bucket@my-namespace/my-artifact-path/test", refresh=True
        )
        assert mock_fs.delete.call_count == 3
        mock_fs.delete.assert_any_call("test/file1")
        mock_fs.delete.assert_any_call("test/file2")
        mock_fs.delete.assert_any_call("test/folder/")

    def test_list_artifacts(self):
        print(os.path.join(self.curr_dir, "artifacts"))

        oci_artifact_repo = OCIObjectStorageArtifactRepository(
            artifact_uri=os.path.join(self.curr_dir, "artifacts")
        )

        artifacts = oci_artifact_repo.list_artifacts()

        expected_artifacts = [
            FileInfo("1.txt", False, 5),
            FileInfo("2.txt", False, 5),
            FileInfo("sub_folder", True, 0),
        ]
        assert artifacts == expected_artifacts


class TestArtifactUploader:
    def test_init(self):
        """Ensures the ArtifactUploader instance can be initialized."""
        artifact_uploader = ArtifactUploader()
        assert isinstance(
            artifact_uploader.upload_manager, object_storage.UploadManager
        )

    @patch.object(object_storage.UploadManager, "upload_file")
    def test_upload(self, mock_upload_file):
        """Tests uploading model artifacts."""
        artifact_uploader = ArtifactUploader()

        local_file = "test_files/test.txt"
        dest_path = "oci://my-bucket@my-namespace/my-artifact-path/logs/test.txt"
        artifact_uploader.upload(local_file, dest_path)

        mock_upload_file.assert_called_with(
            namespace_name="my-namespace",
            bucket_name="my-bucket",
            object_name="my-artifact-path/logs/test.txt",
            file_path=local_file,
        )


class TestUtils:
    """Test static methods in oci_object_storage.py."""

    @patch("os.path.exists")
    def test_get_token_path_in_df(self, mock_path):
        """Tests getting the token path in DF session."""
        mock_path.return_value = True
        assert get_token_path() == DEFAULT_DELEGATION_TOKEN_PATH

    @patch("os.path.exists")
    def test_get_token_path_locally(self, mock_path):
        """Tests getting the token path locally."""
        mock_path.return_value = False
        assert get_token_path() == None

    @patch("oci_mlflow.oci_object_storage.get_delegation_token_signer")
    @patch("ads.common.auth.set_auth")
    def test_get_signer_in_df(self, mock_set_auth, mock_get_signer):
        """Tests getting the storage options in DF session."""
        get_signer(token_path=DEFAULT_DELEGATION_TOKEN_PATH)
        mock_set_auth.assert_called_once_with(
            signer_callable=mock_get_signer,
            signer_kwargs={"token_path": DEFAULT_DELEGATION_TOKEN_PATH},
        )

    @patch("ads.common.auth.default_signer")
    @patch("ads.common.auth.set_auth")
    def test_get_signer_locally(self, mock_set_auth, mock_default_signer):
        """Tests getting the storage options locally."""
        expected_config = {"config": "value", "signer": "value2"}
        mock_default_signer.return_value = expected_config

        signer = get_signer(token_path=None)
        mock_set_auth.assert_not_called()
        assert signer == expected_config
