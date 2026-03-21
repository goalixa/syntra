import subprocess


def get_pods(namespace: str):

    cmd = ["kubectl", "get", "pods", "-n", namespace]

    result = subprocess.run(cmd, capture_output=True, text=True)

    return result.stdout
