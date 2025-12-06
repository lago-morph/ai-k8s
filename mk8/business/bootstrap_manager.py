"""Bootstrap cluster lifecycle management."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import click

from mk8.integrations.kind_client import KindClient, ClusterExistsError, ClusterNotFoundError
from mk8.integrations.kubeconfig import KubeconfigManager
from mk8.integrations.prerequisites import PrerequisiteChecker
from mk8.cli.output import OutputFormatter
from mk8.core.errors import MK8Error


@dataclass
class ClusterStatus:
    """Represents the status of the bootstrap cluster."""

    exists: bool
    name: str = "mk8-bootstrap"
    ready: bool = False
    kubernetes_version: Optional[str] = None
    context_name: Optional[str] = None
    node_count: int = 0
    nodes: List[Dict[str, str]] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)


class BootstrapManager:
    """
    Manages bootstrap cluster lifecycle.

    Coordinates between kind cluster operations, kubeconfig management,
    and prerequisite validation to provide a cohesive bootstrap experience.
    """

    def __init__(
        self,
        kind_client: Optional[KindClient] = None,
        kubeconfig_manager: Optional[KubeconfigManager] = None,
        prerequisite_checker: Optional[PrerequisiteChecker] = None,
        output: Optional[OutputFormatter] = None,
    ):
        """
        Initialize the bootstrap manager.

        Args:
            kind_client: Client for kind operations (created if not provided)
            kubeconfig_manager: Manager for kubeconfig operations (created if not provided)
            prerequisite_checker: Checker for prerequisites (created if not provided)
            output: Output formatter for user feedback
        """
        self.kind_client = kind_client or KindClient()
        self.kubeconfig_manager = kubeconfig_manager or KubeconfigManager()
        self.prerequisite_checker = prerequisite_checker or PrerequisiteChecker()
        self.output = output or OutputFormatter(verbose=False)

    def create_cluster(
        self,
        kubernetes_version: Optional[str] = None,
        force_recreate: bool = False,
    ) -> None:
        """
        Create the bootstrap cluster.

        Args:
            kubernetes_version: Kubernetes version to use (defaults to kind's default)
            force_recreate: If True, delete existing cluster before creating

        Raises:
            MK8Error: If creation fails
        """
        # Validate prerequisites
        self.output.info("Checking prerequisites...")
        self._validate_prerequisites()

        # Check if cluster already exists
        if self.kind_client.cluster_exists():
            if force_recreate:
                self.output.info("Existing cluster found, recreating...")
                try:
                    self.delete_cluster(skip_confirmation=True)
                except Exception as e:
                    self.output.warning(f"Failed to delete existing cluster: {e}")
                    self.output.info("Continuing with creation...")
            else:
                raise ClusterExistsError(
                    f"Bootstrap cluster '{self.kind_client.CLUSTER_NAME}' already exists",
                    suggestions=[
                        "Use 'mk8 bootstrap delete' to remove the existing cluster",
                        "Use --force-recreate flag to automatically recreate",
                        "Use 'mk8 bootstrap status' to check cluster state",
                    ],
                )

        # Create cluster
        self.output.info(f"Creating bootstrap cluster '{self.kind_client.CLUSTER_NAME}'...")
        try:
            self.kind_client.create_cluster(kubernetes_version=kubernetes_version)
        except Exception as e:
            self.output.error(f"Failed to create cluster: {e}")
            raise

        # Wait for cluster to be ready
        self.output.info("Waiting for cluster to be ready...")
        try:
            self.kind_client.wait_for_ready(timeout=300)
        except Exception as e:
            self.output.error(f"Cluster did not become ready: {e}")
            raise

        # Get kubeconfig and merge
        self.output.info("Configuring kubectl access...")
        try:
            kubeconfig_yaml = self.kind_client.get_kubeconfig()
            import yaml

            kubeconfig_data = yaml.safe_load(kubeconfig_yaml)

            # Extract cluster info
            if kubeconfig_data.get("clusters"):
                cluster = kubeconfig_data["clusters"][0]
                cluster_name = cluster["name"]
                cluster_config = cluster["cluster"]

                # Add cluster to kubeconfig
                self.kubeconfig_manager.add_cluster(
                    cluster_name, cluster_config, set_current=True
                )

        except Exception as e:
            self.output.warning(f"Failed to configure kubectl: {e}")
            self.output.info("Cluster created but kubectl configuration may need manual setup")

        # Display success
        context_name = f"kind-{self.kind_client.CLUSTER_NAME}"
        self.output.success(f"✓ Bootstrap cluster created successfully")
        self.output.info(f"  Cluster: {self.kind_client.CLUSTER_NAME}")
        self.output.info(f"  Context: {context_name}")
        self.output.info(f"\nNext steps:")
        self.output.info(f"  • Verify cluster: mk8 bootstrap status")
        self.output.info(f"  • Use kubectl: kubectl get nodes --context {context_name}")

    def delete_cluster(self, skip_confirmation: bool = False) -> None:
        """
        Delete the bootstrap cluster.

        Args:
            skip_confirmation: If True, skip confirmation prompt

        Raises:
            MK8Error: If deletion fails
        """
        # Check if cluster exists
        if not self.kind_client.cluster_exists():
            self.output.info("No bootstrap cluster found")
            return

        # Confirm deletion
        if not skip_confirmation:
            if not click.confirm(
                f"Delete bootstrap cluster '{self.kind_client.CLUSTER_NAME}'?",
                default=False,
            ):
                self.output.info("Deletion cancelled")
                return

        self.output.info(f"Deleting bootstrap cluster '{self.kind_client.CLUSTER_NAME}'...")

        # Track what was cleaned up
        cleaned_up = []
        errors = []

        # Delete kind cluster
        try:
            self.kind_client.delete_cluster()
            cleaned_up.append("kind cluster")
        except Exception as e:
            errors.append(f"Failed to delete kind cluster: {e}")
            self.output.warning(errors[-1])

        # Remove from kubeconfig
        try:
            cluster_name = f"kind-{self.kind_client.CLUSTER_NAME}"
            if self.kubeconfig_manager.cluster_exists(cluster_name):
                self.kubeconfig_manager.remove_cluster(
                    cluster_name, restore_previous_context=True
                )
                cleaned_up.append("kubeconfig context")
        except Exception as e:
            errors.append(f"Failed to clean up kubeconfig: {e}")
            self.output.warning(errors[-1])

        # Display summary
        if cleaned_up:
            self.output.success("✓ Cleanup complete")
            self.output.info(f"  Removed: {', '.join(cleaned_up)}")

        if errors:
            self.output.warning(f"\nSome cleanup steps failed:")
            for error in errors:
                self.output.warning(f"  • {error}")

    def get_status(self) -> ClusterStatus:
        """
        Get the current status of the bootstrap cluster.

        Returns:
            ClusterStatus object with cluster information
        """
        # Check if cluster exists
        if not self.kind_client.cluster_exists():
            return ClusterStatus(exists=False)

        # Get cluster info
        try:
            info = self.kind_client.get_cluster_info()

            # Check if all nodes are ready
            all_ready = all(node["status"] == "Ready" for node in info["nodes"])

            # Build issues list
            issues = []
            if not all_ready:
                not_ready = [
                    node["name"]
                    for node in info["nodes"]
                    if node["status"] != "Ready"
                ]
                issues.append(f"Nodes not ready: {', '.join(not_ready)}")

            return ClusterStatus(
                exists=True,
                ready=all_ready,
                kubernetes_version=info.get("kubernetes_version"),
                context_name=info.get("context"),
                node_count=info.get("node_count", 0),
                nodes=info.get("nodes", []),
                issues=issues,
            )

        except Exception as e:
            return ClusterStatus(
                exists=True,
                ready=False,
                issues=[f"Failed to get cluster info: {e}"],
            )

    def cluster_exists(self) -> bool:
        """
        Check if the bootstrap cluster exists.

        Returns:
            True if cluster exists, False otherwise
        """
        return self.kind_client.cluster_exists()

    def _validate_prerequisites(self) -> None:
        """
        Validate prerequisites before operations.

        Raises:
            MK8Error: If prerequisites are not met
        """
        # Check Docker
        docker_result = self.prerequisite_checker.check_docker()
        if not docker_result.installed:
            raise MK8Error(
                "Docker is not installed",
                suggestions=[
                    "Install Docker Desktop: https://www.docker.com/products/docker-desktop",
                    "On Linux: Install Docker Engine",
                    "Verify installation: docker --version",
                ],
            )
        if not docker_result.running:
            raise MK8Error(
                "Docker daemon is not running",
                suggestions=[
                    "Start Docker Desktop",
                    "On Linux: sudo systemctl start docker",
                    "Verify Docker is running: docker ps",
                ],
            )

        # Check kind
        kind_result = self.prerequisite_checker.check_kind()
        if not kind_result.installed:
            raise MK8Error(
                "kind is not installed",
                suggestions=[
                    "Install kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation",
                    "On macOS: brew install kind",
                    "On Linux: Download from GitHub releases",
                    "Verify installation: kind version",
                ],
            )

        # Check kubectl
        kubectl_result = self.prerequisite_checker.check_kubectl()
        if not kubectl_result.installed:
            raise MK8Error(
                "kubectl is not installed",
                suggestions=[
                    "Install kubectl: https://kubernetes.io/docs/tasks/tools/",
                    "On macOS: brew install kubectl",
                    "On Linux: Use package manager or download binary",
                    "Verify installation: kubectl version --client",
                ],
            )
