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