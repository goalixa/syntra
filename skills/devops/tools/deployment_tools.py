"""
Deployment tools for DevOps skill.

Provides Kubernetes deployment operations including apply, rollback, scale,
and health checks for the DevOpsAgent.
"""

import sys
import os
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.k8s_service import get_k8s_service


class DeploymentTools:
    """Kubernetes deployment operations for DevOpsAgent."""

    def __init__(self):
        self.k8s = get_k8s_service()

    def deploy_manifest(self, manifest_path: str, namespace: str = "default") -> Dict[str, Any]:
        """
        Apply a Kubernetes manifest file.

        Args:
            manifest_path: Path to the manifest file (YAML)
            namespace: Target namespace

        Returns:
            Dict with operation result and status

        Raises:
            FileNotFoundError: If manifest file doesn't exist
            ValueError: If manifest is invalid
        """
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

        with open(manifest_path, 'r') as f:
            manifest_content = f.read()

        # Parse manifest kind and apply accordingly
        import yaml
        try:
            docs = list(yaml.safe_load_all(manifest_content))
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in manifest: {e}")

        results = []
        for doc in docs:
            if doc is None:
                continue

            kind = doc.get('kind', 'Unknown')
            name = doc.get('metadata', {}).get('name', 'unknown')
            result = self._apply_manifest(doc, namespace)
            results.append({
                "kind": kind,
                "name": name,
                "status": result
            })

        return {
            "success": all(r.get("status") == "applied" for r in results),
            "applied": results,
            "namespace": namespace
        }

    def _apply_manifest(self, manifest: Dict, namespace: str) -> str:
        """Apply a single manifest document."""
        kind = manifest.get('kind', '').lower()

        try:
            if kind == 'deployment':
                return self._apply_deployment(manifest, namespace)
            elif kind == 'service':
                return self._apply_service(manifest, namespace)
            elif kind == 'configmap':
                return self._apply_configmap(manifest, namespace)
            elif kind == 'secret':
                return self._apply_secret(manifest, namespace)
            elif kind == 'ingress':
                return self._apply_ingress(manifest, namespace)
            else:
                return f"unsupported_kind:{kind}"
        except Exception as e:
            return f"error:{str(e)}"

    def _apply_deployment(self, manifest: Dict, namespace: str) -> str:
        """Apply a Deployment manifest."""
        # Use kubectl apply via subprocess for now
        import subprocess
        import json

        name = manifest['metadata']['name']
        try:
            result = subprocess.run(
                ['kubectl', 'apply', '-f', '-', '-n', namespace],
                input=yaml.dump(manifest),
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return "applied"
            return f"error:{result.stderr}"
        except Exception as e:
            return f"error:{str(e)}"

    def _apply_service(self, manifest: Dict, namespace: str) -> str:
        """Apply a Service manifest."""
        return self._apply_deployment(manifest, namespace)

    def _apply_configmap(self, manifest: Dict, namespace: str) -> str:
        """Apply a ConfigMap manifest."""
        return self._apply_deployment(manifest, namespace)

    def _apply_secret(self, manifest: Dict, namespace: str) -> str:
        """Apply a Secret manifest."""
        return self._apply_deployment(manifest, namespace)

    def _apply_ingress(self, manifest: Dict, namespace: str) -> str:
        """Apply an Ingress manifest."""
        return self._apply_deployment(manifest, namespace)

    def rollback_deployment(
        self,
        deployment_name: str,
        namespace: str = "default",
        revision: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Rollback a deployment to a previous revision.

        Args:
            deployment_name: Name of the deployment
            namespace: Target namespace
            revision: Specific revision to rollback to (optional)

        Returns:
            Dict with rollback result
        """
        import subprocess

        cmd = ['kubectl', 'rollout', 'undo', f'deployment/{deployment_name}', '-n', namespace]
        if revision:
            cmd.extend(['--to-revision', str(revision)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "success": result.returncode == 0,
                "deployment": deployment_name,
                "namespace": namespace,
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def scale_deployment(
        self,
        deployment_name: str,
        replicas: int,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Scale a deployment to the specified number of replicas.

        Args:
            deployment_name: Name of the deployment
            replicas: Target replica count
            namespace: Target namespace

        Returns:
            Dict with scale result
        """
        import subprocess

        try:
            result = subprocess.run(
                ['kubectl', 'scale', f'deployment/{deployment_name}',
                 '--replicas', str(replicas), '-n', namespace],
                capture_output=True,
                text=True
            )
            return {
                "success": result.returncode == 0,
                "deployment": deployment_name,
                "replicas": replicas,
                "namespace": namespace,
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def check_deployment_health(
        self,
        deployment_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Check deployment health status including replicas and conditions.

        Args:
            deployment_name: Name of the deployment
            namespace: Target namespace

        Returns:
            Dict with deployment health info
        """
        import subprocess
        import json

        try:
            result = subprocess.run(
                ['kubectl', 'get', 'deployment', deployment_name,
                 '-n', namespace, '-o', 'json'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {"success": False, "error": result.stderr}

            deploy = json.loads(result.stdout)

            # Get rollout status
            rollout_result = subprocess.run(
                ['kubectl', 'rollout', 'status', f'deployment/{deployment_name}',
                 '-n', namespace, '--timeout=30s'],
                capture_output=True,
                text=True
            )

            status = "healthy" if rollout_result.returncode == 0 else "unhealthy"

            return {
                "success": True,
                "deployment": deployment_name,
                "namespace": namespace,
                "status": status,
                "replicas": {
                    "desired": deploy['spec']['replicas'],
                    "ready": deploy['status'].get('readyReplicas', 0),
                    "available": deploy['status'].get('availableReplicas', 0),
                    "updated": deploy['status'].get('updatedReplicas', 0)
                },
                "conditions": deploy['status'].get('conditions', [])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restart_deployment(self, deployment_name: str, namespace: str = "default") -> Dict[str, Any]:
        """
        Restart a deployment by rolling it out.

        Args:
            deployment_name: Name of the deployment
            namespace: Target namespace

        Returns:
            Dict with restart result
        """
        import subprocess

        try:
            result = subprocess.run(
                ['kubectl', 'rollout', 'restart', f'deployment/{deployment_name}', '-n', namespace],
                capture_output=True,
                text=True
            )
            return {
                "success": result.returncode == 0,
                "deployment": deployment_name,
                "namespace": namespace,
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_deployment_history(
        self,
        deployment_name: str,
        namespace: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Get deployment revision history.

        Args:
            deployment_name: Name of the deployment
            namespace: Target namespace

        Returns:
            List of revision history entries
        """
        import subprocess
        import json

        try:
            result = subprocess.run(
                ['kubectl', ' rollout', 'history', f'deployment/{deployment_name}',
                 '-n', namespace],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return [{"error": result.stderr}]

            # Parse the output
            revisions = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    revisions.append({
                        "revision": parts[0],
                        "change": ' '.join(parts[1:])
                    })

            return revisions
        except Exception as e:
            return [{"error": str(e)}]