# Monitoring Setup

This folder contains configuration and documentation for monitoring the HealthLang AI MVP system.

## Prometheus
- Used for collecting and storing metrics from the application.
- Configuration file: `monitoring/prometheus/prometheus.yml`

## Grafana
- Used for visualizing metrics and dashboards.
- Place dashboard JSON files in: `monitoring/grafana/dashboards/`

## How to Use
- Ensure Prometheus and Grafana services are running (see `docker-compose.yml`).
- Edit or add configuration files as needed for your monitoring setup. 