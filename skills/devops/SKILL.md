# DevOps Skill for Syntra

## Overview

This skill provides DevOps domain expertise to enhance Syntra's DevOpsAgent with Kubernetes operations, deployment patterns, troubleshooting workflows, and incident resolution.

## Capabilities

- **Kubernetes Operations**: Pod management, deployments, services, configmaps, secrets
- **Deployment Patterns**: Rolling updates, blue-green, canary deployments
- **Troubleshooting**: Log analysis, event inspection, resource diagnostics
- **Incident Resolution**: Common K8s failure patterns and remediation steps

## Tools

- `deployment_tools.py` - Deploy, rollback, scale operations
- `troubleshooting_tools.py` - Pod diagnostics and log analysis
- `config_tools.py` - ConfigMaps and secrets management

## Incident Patterns

See `docs/incident_patterns.md` for known Kubernetes failure patterns and remediation steps.

## Usage

```python
from skills.devops.tools.deployment_tools import DeploymentTools

tools = DeploymentTools()
result = tools.deploy_manifest("deployment.yaml")
```

## Version

Current: 0.1.0

## Integration

This skill is designed to work with Syntra's DevOpsAgent. The agent uses the tools here while following the workflows defined in this SKILL.md.