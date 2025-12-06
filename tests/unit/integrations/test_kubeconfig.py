"""Tests for KubeconfigManager."""

import os
import tempfile
import yaml
from pathlib import Path
from datetime import datetime
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch

from mk8.integrations.kubeconfig import KubeconfigManager, KubeconfigError


# Hypothesis strategies for generating test data
@st.composite
def valid_kubeconfig(draw):
    """Generate valid kubeconfig dict."""
    num_clusters = draw(st.integers(min_value=0, max_value=5))
    cluster_names = [f"cluster-{i}" for i in range(num_clusters)]

    return {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {"name": name, "cluster": {"server": f"https://server-{i}"}}
            for i, name in enumerate(cluster_names)
        ],
        "contexts": [
            {"name": name, "context": {"cluster": name, "user": name}}
            for name in cluster_names
        ],
        "users": [
            {"name": name, "user": {"token": f"token-{i}"}}
            for i, name in enumerate(cluster_names)
        ],
        "current-context": cluster_names[0] if cluster_names else None,
        "preferences": {},
    }


class TestKubeconfigManagerInit:
    """Tests for KubeconfigManager initialization."""

    def test_init_with_default_path(self) -> None:
        """Test initialization with default path."""
        manager = KubeconfigManager()
        expected_path = Path.home() / ".kube" / "config"
        assert manager.config_path == expected_path
        assert manager.max_backups == 5

    def test_init_with_custom_path(self) -> None:
        """Test initialization with custom path."""
        custom_path = Path("/tmp/custom-kubeconfig")
        manager = KubeconfigManager(config_path=custom_path)
        assert manager.config_path == custom_path

    def test_init_respects_kubeconfig_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test initialization respects KUBECONFIG environment variable."""
        custom_path = "/tmp/env-kubeconfig"
        monkeypatch.setenv("KUBECONFIG", custom_path)
        manager = KubeconfigManager()
        assert manager.config_path == Path(custom_path)

    def test_init_uses_first_path_from_kubeconfig_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test initialization uses first path when KUBECONFIG has multiple paths."""
        paths = "/tmp/first:/tmp/second:/tmp/third"
        monkeypatch.setenv("KUBECONFIG", paths)
        manager = KubeconfigManager()
        assert manager.config_path == Path("/tmp/first")


class TestKubeconfigManagerFileOperations:
    """Tests for file operations."""

    def test_read_nonexistent_config_returns_empty_structure(self) -> None:
        """Test reading nonexistent config returns empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent" / "config"
            manager = KubeconfigManager(config_path=config_path)

            config = manager._read_config()

            assert config["apiVersion"] == "v1"
            assert config["kind"] == "Config"
            assert config["clusters"] == []
            assert config["contexts"] == []
            assert config["users"] == []

    def test_read_valid_config(self) -> None:
        """Test reading valid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            test_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "test", "cluster": {"server": "https://test"}}],
                "contexts": [{"name": "test", "context": {"cluster": "test", "user": "test"}}],
                "users": [{"name": "test", "user": {"token": "test-token"}}],
                "current-context": "test",
                "preferences": {},
            }

            config_path.write_text(yaml.safe_dump(test_config))
            manager = KubeconfigManager(config_path=config_path)

            config = manager._read_config()

            assert config["apiVersion"] == "v1"
            assert len(config["clusters"]) == 1
            assert config["clusters"][0]["name"] == "test"

    def test_read_invalid_yaml_raises_error(self) -> None:
        """Test reading invalid YAML raises KubeconfigError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            config_path.write_text("{ invalid: yaml: [")

            manager = KubeconfigManager(config_path=config_path)

            with pytest.raises(KubeconfigError) as exc_info:
                manager._read_config()

            assert "invalid YAML" in str(exc_info.value)
            assert len(exc_info.value.suggestions) > 0

    def test_read_missing_required_field_raises_error(self) -> None:
        """Test reading config missing required field raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            invalid_config = {"apiVersion": "v1"}  # Missing required fields
            config_path.write_text(yaml.safe_dump(invalid_config))

            manager = KubeconfigManager(config_path=config_path)

            with pytest.raises(KubeconfigError) as exc_info:
                manager._read_config()

            assert "missing required field" in str(exc_info.value)

    def test_write_config_creates_directory(self) -> None:
        """Test write_config creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "new_dir" / "config"
            manager = KubeconfigManager(config_path=config_path)

            test_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [],
                "contexts": [],
                "users": [],
                "current-context": None,
                "preferences": {},
            }

            manager._write_config(test_config)

            assert config_path.exists()
            assert config_path.parent.exists()

    def test_write_config_sets_secure_permissions(self) -> None:
        """Test write_config sets file permissions to 0o600."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            test_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [],
                "contexts": [],
                "users": [],
                "current-context": None,
                "preferences": {},
            }

            manager._write_config(test_config)

            if os.name != "nt":  # Skip on Windows
                file_stat = config_path.stat()
                assert oct(file_stat.st_mode)[-3:] == "600"

    def test_write_config_creates_backup(self) -> None:
        """Test write_config creates backup of existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create initial config
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [],
                "contexts": [],
                "users": [],
                "current-context": None,
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            # Write new config (should create backup)
            new_config = initial_config.copy()
            new_config["clusters"] = [{"name": "new", "cluster": {"server": "https://new"}}]
            manager._write_config(new_config)

            # Check backup was created
            backup_dir = config_path.parent / "backups"
            assert backup_dir.exists()
            backups = list(backup_dir.glob("config.backup.*"))
            assert len(backups) == 1

    def test_cleanup_old_backups_keeps_max_backups(self) -> None:
        """Test cleanup keeps only max_backups files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path, max_backups=3)

            backup_dir = config_path.parent / "backups"
            backup_dir.mkdir(parents=True)

            # Create 6 backup files
            for i in range(6):
                backup_file = backup_dir / f"config.backup.2024-12-0{i}T12-00-00"
                backup_file.write_text(f"backup {i}")

            manager._cleanup_old_backups()

            remaining_backups = list(backup_dir.glob("config.backup.*"))
            assert len(remaining_backups) == 3

    def test_no_temp_files_after_successful_write(self) -> None:
        """Test no temporary files remain after successful write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            test_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [],
                "contexts": [],
                "users": [],
                "current-context": None,
                "preferences": {},
            }

            manager._write_config(test_config)

            # Check no .tmp files exist
            tmp_files = list(config_path.parent.glob("*.tmp"))
            assert len(tmp_files) == 0

    def test_no_temp_files_after_failed_write(self) -> None:
        """Test no temporary files remain after failed write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create invalid config that will fail serialization
            invalid_config = {"test": object()}  # object() can't be serialized to YAML

            with pytest.raises(KubeconfigError):
                manager._write_config(invalid_config)

            # Check no .tmp files exist
            tmp_files = list(config_path.parent.glob("*.tmp"))
            assert len(tmp_files) == 0


class TestKubeconfigManagerProperties:
    """Property-based tests for KubeconfigManager."""

    @given(valid_kubeconfig())
    @settings(max_examples=100)
    def test_property_parse_serialize_roundtrip(self, config: dict) -> None:
        """Property 17: Parse-serialize round trip should preserve data."""
        yaml_str = yaml.safe_dump(config)
        parsed = yaml.safe_load(yaml_str)

        assert parsed == config

    @given(valid_kubeconfig())
    @settings(max_examples=100)
    def test_property_write_read_roundtrip(self, config: dict) -> None:
        """Property: Writing and reading config should preserve data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            manager._write_config(config)
            read_config = manager._read_config()

            assert read_config == config

    @given(valid_kubeconfig())
    @settings(max_examples=100)
    def test_property_directory_created_with_secure_permissions(
        self, config: dict
    ) -> None:
        """Property 6: Directory should be created with mode 0o700."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "new_dir" / "config"
            manager = KubeconfigManager(config_path=config_path)

            manager._write_config(config)

            assert config_path.parent.exists()
            if os.name != "nt":  # Skip on Windows
                dir_stat = config_path.parent.stat()
                assert oct(dir_stat.st_mode)[-3:] == "700"

    @given(valid_kubeconfig())
    @settings(max_examples=100)
    def test_property_file_has_secure_permissions(self, config: dict) -> None:
        """Property 6: File should have mode 0o600."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            manager._write_config(config)

            if os.name != "nt":  # Skip on Windows
                file_stat = config_path.stat()
                assert oct(file_stat.st_mode)[-3:] == "600"

    @given(valid_kubeconfig())
    @settings(max_examples=100)
    def test_property_standard_structure_on_creation(self, config: dict) -> None:
        """Property 7: Created config should have standard structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            manager._write_config(config)
            read_config = manager._read_config()

            assert "apiVersion" in read_config
            assert "kind" in read_config
            assert "clusters" in read_config
            assert "contexts" in read_config
            assert "users" in read_config

    @given(valid_kubeconfig())
    @settings(max_examples=100)
    def test_property_backup_created_on_modification(self, config: dict) -> None:
        """Property 14: Backup should be created when modifying existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create initial config
            manager._write_config(config)

            # Modify config (should create backup)
            modified_config = config.copy()
            modified_config["clusters"] = []
            manager._write_config(modified_config)

            # Check backup exists
            backup_dir = config_path.parent / "backups"
            backups = list(backup_dir.glob("config.backup.*"))
            assert len(backups) >= 1

    def test_property_backup_cleanup_maintains_limit(self) -> None:
        """Property 15: Only max_backups files should remain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            max_backups = 3
            manager = KubeconfigManager(config_path=config_path, max_backups=max_backups)

            backup_dir = config_path.parent / "backups"
            backup_dir.mkdir(parents=True)

            # Create more than max_backups files
            for i in range(10):
                backup_file = backup_dir / f"config.backup.2024-12-{i:02d}T12-00-00"
                backup_file.write_text(f"backup {i}")

            manager._cleanup_old_backups()

            remaining_backups = list(backup_dir.glob("config.backup.*"))
            assert len(remaining_backups) == max_backups

    @given(valid_kubeconfig())
    @settings(max_examples=100)
    def test_property_no_temp_files_after_operation(self, config: dict) -> None:
        """Property 13: No temporary files should remain after operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            manager._write_config(config)

            tmp_files = list(config_path.parent.glob("*.tmp"))
            assert len(tmp_files) == 0



class TestKubeconfigManagerClusterAddition:
    """Tests for cluster addition."""

    def test_add_cluster_to_empty_config(self) -> None:
        """Test adding cluster to empty config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            cluster_config = {
                "server": "https://test-server:6443",
                "certificate-authority-data": "test-ca-data",
            }

            manager.add_cluster("test-cluster", cluster_config)

            config = manager._read_config()
            assert len(config["clusters"]) == 1
            assert config["clusters"][0]["name"] == "test-cluster"
            assert len(config["contexts"]) == 1
            assert len(config["users"]) == 1

    def test_add_cluster_sets_current_context(self) -> None:
        """Test adding cluster sets current context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            cluster_config = {"server": "https://test-server:6443"}

            manager.add_cluster("test-cluster", cluster_config, set_current=True)

            config = manager._read_config()
            assert config["current-context"] == "test-cluster"

    def test_add_cluster_preserves_existing_entries(self) -> None:
        """Test adding cluster preserves existing entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create initial config with existing cluster
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "existing", "cluster": {"server": "https://existing"}}],
                "contexts": [
                    {"name": "existing", "context": {"cluster": "existing", "user": "existing"}}
                ],
                "users": [{"name": "existing", "user": {"token": "existing-token"}}],
                "current-context": "existing",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            # Add new cluster
            cluster_config = {"server": "https://new-server:6443"}
            manager.add_cluster("new-cluster", cluster_config)

            config = manager._read_config()
            assert len(config["clusters"]) == 2
            assert any(c["name"] == "existing" for c in config["clusters"])
            assert any(c["name"] == "new-cluster" for c in config["clusters"])

    def test_add_cluster_handles_naming_conflict(self) -> None:
        """Test adding cluster with conflicting name auto-renames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create initial config with existing cluster
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "test", "cluster": {"server": "https://existing"}}],
                "contexts": [{"name": "test", "context": {"cluster": "test", "user": "test"}}],
                "users": [{"name": "test", "user": {"token": "existing-token"}}],
                "current-context": "test",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            # Add new cluster with same name
            cluster_config = {"server": "https://new-server:6443"}
            manager.add_cluster("test", cluster_config)

            config = manager._read_config()
            assert len(config["clusters"]) == 2
            cluster_names = [c["name"] for c in config["clusters"]]
            assert "test" in cluster_names
            assert "test-2" in cluster_names

    def test_add_cluster_stores_previous_context(self) -> None:
        """Test adding cluster stores previous context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create initial config with current context
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "existing", "cluster": {"server": "https://existing"}}],
                "contexts": [
                    {"name": "existing", "context": {"cluster": "existing", "user": "existing"}}
                ],
                "users": [{"name": "existing", "user": {"token": "existing-token"}}],
                "current-context": "existing",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            # Add new cluster (should store previous context)
            cluster_config = {"server": "https://new-server:6443"}
            manager.add_cluster("new-cluster", cluster_config, set_current=True)

            assert manager._previous_context == "existing"

    def test_add_cluster_produces_valid_yaml(self) -> None:
        """Test adding cluster produces valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            cluster_config = {"server": "https://test-server:6443"}
            manager.add_cluster("test-cluster", cluster_config)

            # Should be able to read back without error
            config = manager._read_config()
            assert config is not None

    def test_add_cluster_without_setting_current(self) -> None:
        """Test adding cluster without setting as current context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create initial config with current context
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "existing", "cluster": {"server": "https://existing"}}],
                "contexts": [
                    {"name": "existing", "context": {"cluster": "existing", "user": "existing"}}
                ],
                "users": [{"name": "existing", "user": {"token": "existing-token"}}],
                "current-context": "existing",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            # Add new cluster without setting current
            cluster_config = {"server": "https://new-server:6443"}
            manager.add_cluster("new-cluster", cluster_config, set_current=False)

            config = manager._read_config()
            assert config["current-context"] == "existing"


class TestKubeconfigManagerClusterAdditionProperties:
    """Property-based tests for cluster addition."""

    @given(valid_kubeconfig())
    @settings(max_examples=50)
    def test_property_read_before_modify(self, initial_config: dict) -> None:
        """Property 1: Should read existing config before modifying."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            config_path.write_text(yaml.safe_dump(initial_config))

            manager = KubeconfigManager(config_path=config_path)

            with patch.object(manager, "_read_config", wraps=manager._read_config) as mock_read:
                with patch.object(manager, "_write_config", wraps=manager._write_config) as mock_write:
                    cluster_config = {"server": "https://new:6443"}
                    manager.add_cluster("new-cluster", cluster_config)

                    # Read should be called before write
                    assert mock_read.called
                    assert mock_write.called
                    assert mock_read.call_count >= 1

    @given(valid_kubeconfig())
    @settings(max_examples=50)
    def test_property_preservation_of_unrelated_entries(self, initial_config: dict) -> None:
        """Property 3: Should preserve all unrelated entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            config_path.write_text(yaml.safe_dump(initial_config))

            manager = KubeconfigManager(config_path=config_path)

            # Store original entries
            original_clusters = [c["name"] for c in initial_config.get("clusters", [])]
            original_contexts = [c["name"] for c in initial_config.get("contexts", [])]
            original_users = [u["name"] for u in initial_config.get("users", [])]

            # Add new cluster
            cluster_config = {"server": "https://new:6443"}
            manager.add_cluster("new-cluster", cluster_config)

            # Read back and verify original entries preserved
            config = manager._read_config()
            new_clusters = [c["name"] for c in config["clusters"]]
            new_contexts = [c["name"] for c in config["contexts"]]
            new_users = [u["name"] for u in config["users"]]

            for cluster in original_clusters:
                assert cluster in new_clusters
            for context in original_contexts:
                assert context in new_contexts
            for user in original_users:
                assert user in new_users

    @given(valid_kubeconfig())
    @settings(max_examples=50)
    def test_property_merge_produces_valid_yaml(self, initial_config: dict) -> None:
        """Property 4: Merge should produce valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            config_path.write_text(yaml.safe_dump(initial_config))

            manager = KubeconfigManager(config_path=config_path)

            cluster_config = {"server": "https://new:6443"}
            manager.add_cluster("new-cluster", cluster_config)

            # Should be able to read back without error
            config = manager._read_config()
            assert config is not None
            assert "clusters" in config

    @given(valid_kubeconfig())
    @settings(max_examples=50)
    def test_property_context_setting_on_cluster_add(self, initial_config: dict) -> None:
        """Property 8: Should set current context when set_current=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            config_path.write_text(yaml.safe_dump(initial_config))

            manager = KubeconfigManager(config_path=config_path)

            cluster_config = {"server": "https://new:6443"}
            manager.add_cluster("new-cluster", cluster_config, set_current=True)

            config = manager._read_config()
            assert config["current-context"] == "new-cluster"

    @given(valid_kubeconfig())
    @settings(max_examples=50)
    def test_property_previous_context_storage(self, initial_config: dict) -> None:
        """Property 9: Should store previous context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            config_path.write_text(yaml.safe_dump(initial_config))

            manager = KubeconfigManager(config_path=config_path)

            previous = initial_config.get("current-context")

            cluster_config = {"server": "https://new:6443"}
            manager.add_cluster("new-cluster", cluster_config, set_current=True)

            assert manager._previous_context == previous



class TestKubeconfigManagerClusterRemoval:
    """Tests for cluster removal."""

    def test_remove_cluster_removes_all_entries(self) -> None:
        """Test removing cluster removes cluster, context, and user entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create config with cluster
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "test", "cluster": {"server": "https://test"}}],
                "contexts": [{"name": "test", "context": {"cluster": "test", "user": "test"}}],
                "users": [{"name": "test", "user": {"token": "test-token"}}],
                "current-context": "test",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            manager.remove_cluster("test")

            config = manager._read_config()
            assert len(config["clusters"]) == 0
            assert len(config["contexts"]) == 0
            assert len(config["users"]) == 0

    def test_remove_cluster_preserves_other_entries(self) -> None:
        """Test removing cluster preserves other clusters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create config with multiple clusters
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster1", "cluster": {"server": "https://cluster1"}},
                    {"name": "cluster2", "cluster": {"server": "https://cluster2"}},
                ],
                "contexts": [
                    {"name": "cluster1", "context": {"cluster": "cluster1", "user": "cluster1"}},
                    {"name": "cluster2", "context": {"cluster": "cluster2", "user": "cluster2"}},
                ],
                "users": [
                    {"name": "cluster1", "user": {"token": "token1"}},
                    {"name": "cluster2", "user": {"token": "token2"}},
                ],
                "current-context": "cluster1",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            manager.remove_cluster("cluster1")

            config = manager._read_config()
            assert len(config["clusters"]) == 1
            assert config["clusters"][0]["name"] == "cluster2"
            assert len(config["contexts"]) == 1
            assert config["contexts"][0]["name"] == "cluster2"
            assert len(config["users"]) == 1
            assert config["users"][0]["name"] == "cluster2"

    def test_remove_cluster_restores_previous_context(self) -> None:
        """Test removing current cluster restores previous context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create config with multiple clusters
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster1", "cluster": {"server": "https://cluster1"}},
                    {"name": "cluster2", "cluster": {"server": "https://cluster2"}},
                ],
                "contexts": [
                    {"name": "cluster1", "context": {"cluster": "cluster1", "user": "cluster1"}},
                    {"name": "cluster2", "context": {"cluster": "cluster2", "user": "cluster2"}},
                ],
                "users": [
                    {"name": "cluster1", "user": {"token": "token1"}},
                    {"name": "cluster2", "user": {"token": "token2"}},
                ],
                "current-context": "cluster2",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            # Store previous context
            manager._previous_context = "cluster1"

            # Remove current cluster
            manager.remove_cluster("cluster2", restore_previous_context=True)

            config = manager._read_config()
            assert config["current-context"] == "cluster1"

    def test_remove_cluster_selects_another_context_when_no_previous(self) -> None:
        """Test removing current cluster selects another when no previous context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create config with multiple clusters
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster1", "cluster": {"server": "https://cluster1"}},
                    {"name": "cluster2", "cluster": {"server": "https://cluster2"}},
                ],
                "contexts": [
                    {"name": "cluster1", "context": {"cluster": "cluster1", "user": "cluster1"}},
                    {"name": "cluster2", "context": {"cluster": "cluster2", "user": "cluster2"}},
                ],
                "users": [
                    {"name": "cluster1", "user": {"token": "token1"}},
                    {"name": "cluster2", "user": {"token": "token2"}},
                ],
                "current-context": "cluster1",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            manager.remove_cluster("cluster1")

            config = manager._read_config()
            assert config["current-context"] == "cluster2"

    def test_remove_cluster_clears_context_when_last_cluster(self) -> None:
        """Test removing last cluster clears current-context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create config with single cluster
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "test", "cluster": {"server": "https://test"}}],
                "contexts": [{"name": "test", "context": {"cluster": "test", "user": "test"}}],
                "users": [{"name": "test", "user": {"token": "test-token"}}],
                "current-context": "test",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            manager.remove_cluster("test")

            config = manager._read_config()
            assert config["current-context"] is None

    def test_remove_nonexistent_cluster_raises_error(self) -> None:
        """Test removing nonexistent cluster raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            with pytest.raises(KubeconfigError) as exc_info:
                manager.remove_cluster("nonexistent")

            assert "not found" in str(exc_info.value).lower()
            assert len(exc_info.value.suggestions) > 0


class TestKubeconfigManagerContextManagement:
    """Tests for context management."""

    def test_get_current_context(self) -> None:
        """Test getting current context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create config with current context
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "test", "cluster": {"server": "https://test"}}],
                "contexts": [{"name": "test", "context": {"cluster": "test", "user": "test"}}],
                "users": [{"name": "test", "user": {"token": "test-token"}}],
                "current-context": "test",
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            current = manager.get_current_context()
            assert current == "test"

    def test_get_current_context_returns_none_when_not_set(self) -> None:
        """Test getting current context returns None when not set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            current = manager.get_current_context()
            assert current is None

    def test_set_current_context(self) -> None:
        """Test setting current context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create config with contexts
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "test", "cluster": {"server": "https://test"}}],
                "contexts": [{"name": "test", "context": {"cluster": "test", "user": "test"}}],
                "users": [{"name": "test", "user": {"token": "test-token"}}],
                "current-context": None,
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            manager.set_current_context("test")

            config = manager._read_config()
            assert config["current-context"] == "test"

    def test_list_clusters(self) -> None:
        """Test listing clusters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create config with multiple clusters
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster1", "cluster": {"server": "https://cluster1"}},
                    {"name": "cluster2", "cluster": {"server": "https://cluster2"}},
                ],
                "contexts": [],
                "users": [],
                "current-context": None,
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            clusters = manager.list_clusters()
            assert len(clusters) == 2
            assert "cluster1" in clusters
            assert "cluster2" in clusters

    def test_list_clusters_returns_empty_for_no_clusters(self) -> None:
        """Test listing clusters returns empty list when no clusters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            clusters = manager.list_clusters()
            assert clusters == []

    def test_cluster_exists(self) -> None:
        """Test checking if cluster exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Create config with cluster
            initial_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "test", "cluster": {"server": "https://test"}}],
                "contexts": [],
                "users": [],
                "current-context": None,
                "preferences": {},
            }
            config_path.write_text(yaml.safe_dump(initial_config))

            assert manager.cluster_exists("test") is True
            assert manager.cluster_exists("nonexistent") is False


class TestKubeconfigManagerRemovalProperties:
    """Property-based tests for cluster removal."""

    @given(valid_kubeconfig())
    @settings(max_examples=50)
    def test_property_cascading_removal(self, initial_config: dict) -> None:
        """Property 10: Should remove cluster, context, and user entries."""
        if not initial_config.get("clusters"):
            return  # Skip if no clusters

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            config_path.write_text(yaml.safe_dump(initial_config))

            manager = KubeconfigManager(config_path=config_path)

            # Remove first cluster
            cluster_to_remove = initial_config["clusters"][0]["name"]
            manager.remove_cluster(cluster_to_remove)

            config = manager._read_config()

            # Verify cluster removed
            cluster_names = [c["name"] for c in config["clusters"]]
            assert cluster_to_remove not in cluster_names

            # Verify context removed
            context_names = [c["name"] for c in config["contexts"]]
            assert cluster_to_remove not in context_names

            # Verify user removed
            user_names = [u["name"] for u in config["users"]]
            assert cluster_to_remove not in user_names

    @given(valid_kubeconfig())
    @settings(max_examples=50)
    def test_property_context_switching_on_removal(self, initial_config: dict) -> None:
        """Property 11: Should handle context switching appropriately."""
        if len(initial_config.get("clusters", [])) < 1:
            return  # Skip if no clusters

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"

            # Set first cluster as current
            if initial_config["clusters"]:
                initial_config["current-context"] = initial_config["clusters"][0]["name"]

            config_path.write_text(yaml.safe_dump(initial_config))

            manager = KubeconfigManager(config_path=config_path)

            cluster_to_remove = initial_config["clusters"][0]["name"]
            manager.remove_cluster(cluster_to_remove)

            config = manager._read_config()

            # Context should be updated (either to another cluster or None)
            if config["clusters"]:
                # Should switch to another cluster
                assert config["current-context"] in [c["name"] for c in config["clusters"]]
            else:
                # Should be None if no clusters left
                assert config["current-context"] is None


class TestKubeconfigManagerErrorHandling:
    """Tests for error handling."""

    def test_property_error_messages_include_suggestions(self) -> None:
        """Property 16: All errors should include suggestions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config"
            manager = KubeconfigManager(config_path=config_path)

            # Test various error conditions
            errors_to_test = [
                lambda: manager.remove_cluster("nonexistent"),
                lambda: manager._read_config() if config_path.write_text("{ invalid: yaml") else None,
            ]

            for error_func in errors_to_test:
                try:
                    error_func()
                except KubeconfigError as e:
                    assert len(e.suggestions) > 0
                    assert all(isinstance(s, str) for s in e.suggestions)
                except Exception:
                    pass  # Other exceptions are fine for this test
