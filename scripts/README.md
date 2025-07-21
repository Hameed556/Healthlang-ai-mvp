# Scripts

This directory contains utility scripts for HealthLang AI MVP.

## Contents

### Development Scripts
- **setup.sh** - Initial project setup
- **install-dependencies.sh** - Install all dependencies
- **setup-database.sh** - Database initialization
- **seed-data.sh** - Populate with sample data

### Deployment Scripts
- **deploy.sh** - Production deployment
- **rollback.sh** - Deployment rollback
- **health-check.sh** - System health verification
- **backup.sh** - Database and data backup

### Maintenance Scripts
- **cleanup.sh** - Clean temporary files
- **update-models.sh** - Update ML models
- **sync-data.sh** - Sync medical knowledge base
- **monitor-logs.sh** - Log monitoring and analysis

### Utility Scripts
- **generate-keys.sh** - Generate API keys
- **migrate-db.sh** - Database migrations
- **test-all.sh** - Run all tests
- **benchmark.sh** - Performance benchmarking

## Usage

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run setup
./scripts/setup.sh

# Deploy to production
./scripts/deploy.sh

# Run health check
./scripts/health-check.sh
```

## Script Categories

- **Setup & Installation** - Project initialization
- **Deployment & Operations** - Production management
- **Data Management** - Database and data operations
- **Monitoring & Maintenance** - System maintenance
- **Testing & Quality** - Quality assurance 