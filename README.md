# GameContainerManager

It's a docker image base on Python 3.9 to be able to do the first maintenance of your docker's *games* containers

## How to deploy it ?

⚠️**You need to build the image localy**⚠️ there is no image available on registry

For build image locally, run: 

`docker build --pull --rm -f 'PATH/OF/YOUR/FOLDER/Dockerfile' -t 'gamecontainermanager:latest' 'PATH/OF/YOUR/FOLDER'`

To see it yo can run `docker image ls`

| REPOSITORY | TAG | IMAGE ID | CREATED | SIZE |
|------------|-----|----------|---------|------|
| gamecontainermanager | latest | 195ae66bdf6a | About a minute ago | 182MB |

Fill a file `.env` at the root of `PATH/OF/YOUR/FOLDER` with desire vars (see below) and deploy services

## Variables
| Name | Service Assosiate | Mandatory | Default Value | Value Possible| UTILITIES |
|------|-------------------|-----------|---------------|---------------|-----------|
| DOCKERCONTAINERMANAGER_BACKEND_URL | bot, frontend | ✅ | http://backend:5000 | *http://your.service.name:5000* | Url for your backend container (can be in local network of docker) |
| DOCKERCONTAINERMANAGER_DEBUG | All | ❌ | False | `False` // `True` | Enable debug logs level |
| DOCKERCONTAINERMANAGER_DISCORD_TOKEN | bot | ✅ | False | *YOUR_DISCORD_TOKEN* | Discord auth token for bot see (Discord doc)[https://discord.com/developers/docs/intro] |
| DOCKERCONTAINERMANAGER_FRONTEND_URL | bot | ❌ | http://backend:5000 | *https://your.domain.com* | Address of your frontend service is reachable |
| DOCKERCONTAINERMANAGER_SERVICE_TYPE | backend, bot, frontend | ✅ | **NONE** | `backend`, `bot`, `frontend` | Name of service wanted to run |