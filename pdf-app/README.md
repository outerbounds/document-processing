## Prerequisites

### Option 1: [Install Docker](https://docs.docker.com/engine/install/)


### Option 2: Install node and Python

## Setup

The goal is to deploy 2 services: a backend service and a frontend service.
- The backend service is a FastAPI service that will interact with OpenAI API.
- The frontend service is a SvelteKit application.

### Set OpenAI key

Create a file call `.env` in the root directory and put only your OpenAI key in it.
`docker-compose.yml` will include this file's variables to the `backend` container environment.

## Run manually

### Start backend
```
cd pdf-app/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Run frontend
```
cd pdf-app/frontend
npm run dev
```

## Dev

### Pull pre-built containers

```
docker pull docker.io/eddieob/pdf-app-frontend:latest
docker pull docker.io/eddieob/pdf-app-frontend:latest
```

### Build with docker compose

With container built:
```
docker compose up --build
```

After you have the containers built once, remove `--build` to start the containers faster:
```
docker compose up
```
