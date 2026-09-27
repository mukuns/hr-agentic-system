# Deployment Notes

## Deployment status

This workspace contains a fully working local implementation and a deployment-ready architecture, but no live public URL has been created from this environment because deployment credentials and hosting setup were not provided here.

The project is designed to be deployed as a single-service free-tier app on Render or Railway using:

- the FastAPI web app
- the local MCP server and client
- SQLite mock data
- the local policy corpus and retrieval layer

## Recommended deployment configuration

- Service type: web service
- Runtime: Python
- Command: `uvicorn src.api:app --host 0.0.0.0 --port 8000`
- Environment variables:
  - `PORT`
  - optional LLM provider keys if future upgrade uses an external model
  - any secrets for hosted deployments

## Expected cold start behavior

Because the service is intended for free-tier hosting, cold starts may occur after inactivity.

Expected behavior:

- first request after idle may take 20-60 seconds
- warm requests should return within a few seconds
- local SQLite and policy corpus remain inside the app environment for persistence

## Live URL placeholder

- Live URL: not yet provisioned in this workspace
- Health endpoint: not yet available from a public host

Once a hosting provider is configured, replace this file with the actual public URL and the health endpoint output.
