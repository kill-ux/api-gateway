# API Gateway

A lightweight Flask-based gateway that fronts the `inventory-app` and `billing-app` services, exposes a single public API, and handles async order processing through RabbitMQ.

This service is designed to be the entrypoint for the Code-Keeper microservices platform and is packaged as a Docker image for deployment behind the shared AWS ALB.

## Overview

The gateway performs two main roles:

- Proxies incoming requests to the inventory service under `/api/movies`
- Forwards billing-related requests and enqueues order messages to RabbitMQ for background processing

It also exposes a simple health endpoint for load balancers and monitoring.

## Architecture

```text
Client
  │
  ▼
API Gateway
  ├── /api/movies/*  ──> inventory-app
  ├── /api/billing    ──> billing-app (GET)
  └── /api/billing    ──> RabbitMQ (POST order)
```

## Features

- Request proxying for inventory endpoints
- Direct billing GET forwarding
- Async order submission to RabbitMQ
- Containerized deployment with Docker
- Health checks for orchestration platforms
- CI pipeline with unit/integration tests and SonarQube scanning

## Project Structure

```text
api-gateway/
├── app/
│   ├── __init__.py
│   └── routes.py
├── tests/
│   ├── unit/
│   └── integration/
├── .gitlab-ci.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── server.py
├── sonar-project.properties
└── logo.png
```

## Prerequisites

- Python 3.12+
- pip
- Docker (optional, for local container runs)
- Access to the downstream services and RabbitMQ instance

## Configuration

The application reads environment variables at startup. A typical `.env` file looks like:

```env
APIGATEWAY_PORT=3000
INVENTORY_APP_HOST=inventory-app
INVENTORY_APP_PORT=5000
BILLING_APP_HOST=billing-app
BILLING_APP_PORT=5001
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_QUEUE=orders
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
```

Required variables:

- `APIGATEWAY_PORT`
- `INVENTORY_APP_HOST`
- `INVENTORY_APP_PORT`
- `BILLING_APP_HOST`
- `BILLING_APP_PORT`
- `RABBITMQ_HOST`
- `RABBITMQ_PORT`
- `RABBITMQ_QUEUE`
- `RABBITMQ_USER`
- `RABBITMQ_PASS`

## Local Development

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Run the gateway locally:

```bash
python server.py
```

By default, the app listens on the port configured by `APIGATEWAY_PORT` and exposes the service on `0.0.0.0`.

## Docker

Build the container:

```bash
docker build -t api-gateway .
```

Run it:

```bash
docker run --rm -p 3000:3000 --env-file .env api-gateway
```

The container image starts the app using the `server.py` entrypoint and includes a health check against `/health`.

## API Endpoints

### Health

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "version": "v1.1.8"
}
```

### Inventory Proxy

All requests under `/api/movies` are forwarded to the inventory service.

```http
GET /api/movies/
POST /api/movies/
DELETE /api/movies/
GET /api/movies/<path:subpath>
POST /api/movies/<path:subpath>
PUT /api/movies/<path:subpath>
DELETE /api/movies/<path:subpath>
```

### Billing Proxy

```http
GET /api/billing/
POST /api/billing/
```

Behavior:

- `GET /api/billing/` proxies the request to the billing service
- `POST /api/billing/` validates payload fields and pushes an order message to RabbitMQ

Expected payload for order submission:

```json
{
  "user_id": "123",
  "number_of_items": 3,
  "total_amount": 49.99
}
```

A successful enqueue returns:

```json
{
  "message": "Order request accepted"
}
```

## Testing

Run the unit tests:

```bash
pytest -v tests/unit --cov=app --cov-report=term
```

Run the integration tests:

```bash
docker compose -f tests/integration/docker-compose.yml up -d --wait
pytest -v tests/integration
docker compose -f tests/integration/docker-compose.yml down --rmi local
```

## CI/CD

This project includes a GitLab CI pipeline configured in `.gitlab-ci.yml`.

Pipeline stages:

- build
- test
- scan
- package
- deploy

The pipeline performs:

- dependency installation
- Python compilation checks
- unit and integration tests
- SonarQube analysis
- Trivy vulnerability scanning
- Docker image packaging and ECS deployment for staging/production
