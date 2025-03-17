# Building a Jupyter Environment

## Introduction

It is helpful to have a custom Jupyter environment for your students to access. This can be easily done by creating a container.

## Setting up the Environment

### Step 1: Install Docker

You must have docker installed on your local computer. If you do not have it installed, you can download it from the [Docker website](https://www.docker.com/products/docker-desktop).

:exclamation: make sure you have setup your docker account and have logged in to the docker desktop application.

### Step 2: View the Dockerfile

There is a template docker file located in the `custom_env` folder. You can use this file as a starting point for your custom environment. This pulls a base image of `jupyter`, there is a requirements file that installs the necessary packages, and then it sets the working directory and the command to run the Jupyter notebook.

### Step 3: Build the Docker Image

#### Build Docker Image

```bash
. ./secrets.sh &&
tagname=$envtag &&
docker build -t $dockeruser/$envcontainer:$envtag ./custom_env &&
docker push $dockeruser/$envcontainer:$envtag &&
docker tag $dockeruser/$envcontainer:$envtag $dockeruser/$envcontainer:latest &&
docker push $dockeruser/$envcontainer:latest
```

#### Alternative build for NRP

```bash
. ./secrets.sh &&
tagname=$envtag &&
docker build -t gitlab-registry.nrp-nautilus.io/$nrpgitlabuser/$envcontainer:$envtag ./custom_env &&
docker push gitlab-registry.nrp-nautilus.io/$nrpgitlabuser/$envcontainer:$envtag &&
docker tag gitlab-registry.nrp-nautilus.io/$nrpgitlabuser/ $envcontainer:$envtag gitlab-registry.nrp-nautilus.io/$nrpgitlabuser/$envcontainer:latest &&
docker push gitlab-registry.nrp-nautilus.io/$nrpgitlabuser/$envcontainer:latest
```
