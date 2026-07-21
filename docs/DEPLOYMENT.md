# Deployment Guide

## Pilot server

Minimum practical pilot server:

- 2 vCPU
- 4 GB RAM
- 20 GB encrypted storage
- Ubuntu LTS or any Docker-capable host
- HTTPS reverse proxy

## Commands

```bash
cp .env.example .env
# edit .env
docker compose up -d --build
```

## Reverse proxy

Terminate TLS in Nginx, Caddy, or the university ingress. Only expose port 443 publicly. Keep the application container on a private network.

## Backup

Back up the Docker volume or these paths:

- `/data/daneshyar.sqlite3`
- `/data/uploads`
- `/data/exports`

## Production hardening checklist

- Add university SSO and role-based access
- Encrypt disks and backups
- Define document retention and deletion policy
- Add request throttling and malware scanning
- Restrict upload size and content type at the reverse proxy
- Centralize logs without storing API keys or sensitive student text
- Run dependency and container image scans
