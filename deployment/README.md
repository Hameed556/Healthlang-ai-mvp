# Deployment

This directory contains deployment configurations for HealthLang AI MVP.

## Contents

- **Kubernetes manifests** - K8s deployment configurations
- **Helm charts** - Helm package for K8s deployment
- **CI/CD pipelines** - GitHub Actions, GitLab CI, etc.
- **Infrastructure as Code** - Terraform, CloudFormation
- **Environment configurations** - Production, staging, development

## Deployment Options

### Docker Compose (Development)
```bash
make deploy-dev
```

### Kubernetes (Production)
```bash
make deploy-prod
```

### Cloud Platforms
- AWS ECS/EKS
- Google Cloud Run/GKE
- Azure Container Instances/AKS

## Environment Variables

See `../env.example` for required environment variables.

## Monitoring

Deployment includes:
- Health checks
- Auto-scaling
- Load balancing
- SSL/TLS termination 