"""
Configuration tools for DevOps skill.

Provides ConfigMap and Secret management operations for Kubernetes resources.
"""

import sys
import os
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.k8s_service import get_k8s_service


class ConfigTools:
    """Kubernetes configuration management for DevOpsAgent."""

    def __init__(self):
        self.k8s = get_k8s_service()

    def get_configmap(
        self,
        configmap_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Get a ConfigMap and its data.

        Args:
            configmap_name: Name of the ConfigMap
            namespace: Target namespace

        Returns:
            Dict with ConfigMap data
        """
        import subprocess
        import json

        try:
            result = subprocess.run(
                ['kubectl', 'get', 'configmap', configmap_name,
                 '-n', namespace, '-o', 'json'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {"success": False, "error": result.stderr}

            cm = json.loads(result.stdout)
            return {
                "success": True,
                "name": cm['metadata']['name'],
                "namespace": namespace,
                "data": cm.get('data', {}),
                "binary_data": cm.get('binaryData', {}),
                "created": cm['metadata'].get('creationTimestamp', '')
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_configmap(
        self,
        configmap_name: str,
        data: Dict[str, str],
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Update a ConfigMap with new data.

        Args:
            configmap_name: Name of the ConfigMap
            data: Dictionary of key-value pairs to update
            namespace: Target namespace

        Returns:
            Dict with update result
        """
        import subprocess

        # Get existing ConfigMap
        existing = self.get_configmap(configmap_name, namespace)
        if not existing.get('success'):
            return existing

        # Merge data
        new_data = existing.get('data', {})
        new_data.update(data)

        # Create new manifest
        manifest = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': configmap_name,
                'namespace': namespace
            },
            'data': new_data
        }

        import yaml
        try:
            result = subprocess.run(
                ['kubectl', 'apply', '-f', '-', '-n', namespace],
                input=yaml.dump(manifest),
                capture_output=True,
                text=True
            )

            return {
                "success": result.returncode == 0,
                "configmap": configmap_name,
                "namespace": namespace,
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_configmap_from_file(
        self,
        configmap_name: str,
        file_path: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Create a ConfigMap from a file.

        Args:
            configmap_name: Name for the ConfigMap
            file_path: Path to the file
            namespace: Target namespace

        Returns:
            Dict with create result
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        import subprocess
        try:
            result = subprocess.run(
                ['kubectl', 'create', 'configmap', configmap_name,
                 f'--from-file={os.path.basename(file_path)}={file_path}',
                 '-n', namespace],
                capture_output=True,
                text=True
            )

            return {
                "success": result.returncode == 0,
                "configmap": configmap_name,
                "namespace": namespace,
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_secret(
        self,
        secret_name: str,
        namespace: str = "default",
        decode: bool = True
    ) -> Dict[str, Any]:
        """
        Get a Secret (optionally decoded).

        Args:
            secret_name: Name of the Secret
            namespace: Target namespace
            decode: Whether to decode base64 values

        Returns:
            Dict with Secret data
        """
        import subprocess
        import json

        try:
            result = subprocess.run(
                ['kubectl', 'get', 'secret', secret_name,
                 '-n', namespace, '-o', 'json'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {"success": False, "error": result.stderr}

            secret = json.loads(result.stdout)

            data = secret.get('data', {})

            if decode:
                import base64
                decoded = {}
                for key, value in data.items():
                    try:
                        decoded[key] = base64.b64decode(value).decode('utf-8')
                    except Exception:
                        decoded[key] = value  # Keep original if decode fails
                data = decoded

            return {
                "success": True,
                "name": secret['metadata']['name'],
                "namespace": namespace,
                "type": secret.get('type', 'Opaque'),
                "data": data,
                "created": secret['metadata'].get('creationTimestamp', '')
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_secret(
        self,
        secret_name: str,
        data: Dict[str, str],
        secret_type: str = "Opaque",
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Create a Secret with the given data.

        Args:
            secret_name: Name for the Secret
            data: Dictionary of key-value pairs
            secret_type: Type of secret (Opaque, docker-registry, tls, etc.)
            namespace: Target namespace

        Returns:
            Dict with create result
        """
        import base64
        import yaml
        import subprocess

        # Encode values to base64
        encoded_data = {}
        for key, value in data.items():
            encoded_data[key] = base64.b64encode(value.encode('utf-8')).decode('utf-8')

        manifest = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': secret_name,
                'namespace': namespace
            },
            'type': secret_type,
            'data': encoded_data
        }

        try:
            result = subprocess.run(
                ['kubectl', 'apply', '-f', '-', '-n', namespace],
                input=yaml.dump(manifest),
                capture_output=True,
                text=True
            )

            return {
                "success": result.returncode == 0,
                "secret": secret_name,
                "namespace": namespace,
                "type": secret_type,
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_configmaps(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """
        List all ConfigMaps in a namespace.

        Args:
            namespace: Target namespace

        Returns:
            List of ConfigMap summaries
        """
        import subprocess
        import json

        try:
            result = subprocess.run(
                ['kubectl', 'get', 'configmaps', '-n', namespace, '-o', 'json'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return [{"error": result.stderr}]

            cms = json.loads(result.stdout).get('items', [])
            return [
                {
                    "name": cm['metadata']['name'],
                    "created": cm['metadata'].get('creationTimestamp', ''),
                    "keys": list(cm.get('data', {}).keys())
                }
                for cm in cms
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def list_secrets(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """
        List all Secrets in a namespace.

        Args:
            namespace: Target namespace

        Returns:
            List of Secret summaries
        """
        import subprocess
        import json

        try:
            result = subprocess.run(
                ['kubectl', 'get', 'secrets', '-n', namespace, '-o', 'json'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return [{"error": result.stderr}]

            secrets = json.loads(result.stdout).get('items', [])
            return [
                {
                    "name": s['metadata']['name'],
                    "type": s.get('type', 'Opaque'),
                    "created": s['metadata'].get('creationTimestamp', '')
                }
                for s in secrets
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def compare_configmap(
        self,
        configmap_name: str,
        namespace1: str,
        namespace2: str
    ) -> Dict[str, Any]:
        """
        Compare a ConfigMap between two namespaces.

        Args:
            configmap_name: Name of the ConfigMap
            namespace1: First namespace
            namespace2: Second namespace

        Returns:
            Dict with comparison results
        """
        cm1 = self.get_configmap(configmap_name, namespace1)
        cm2 = self.get_configmap(configmap_name, namespace2)

        if not cm1.get('success') or not cm2.get('success'):
            return {
                "success": False,
                "error": "Could not fetch one or both ConfigMaps"
            }

        data1 = cm1.get('data', {})
        data2 = cm2.get('data', {})

        all_keys = set(data1.keys()) | set(data2.keys())
        differences = []

        for key in all_keys:
            if key not in data1:
                differences.append({"key": key, "status": "only_in_namespace2"})
            elif key not in data2:
                differences.append({"key": key, "status": "only_in_namespace1"})
            elif data1[key] != data2[key]:
                differences.append({
                    "key": key,
                    "status": "different",
                    "namespace1": data1[key][:50] + "..." if len(data1[key]) > 50 else data1[key],
                    "namespace2": data2[key][:50] + "..." if len(data2[key]) > 50 else data2[key]
                })

        return {
            "success": True,
            "configmap": configmap_name,
            "namespace1": namespace1,
            "namespace2": namespace2,
            "identical": len(differences) == 0,
            "differences": differences
        }