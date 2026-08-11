# tests/integration/hoverfly.Dockerfile
FROM spectolabs/hoverfly:latest
COPY mocks/inventory.json /hoverfly/inventory.json