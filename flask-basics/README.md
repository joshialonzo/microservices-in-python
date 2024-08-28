# Basic Microservices in Python

* Installing Python 3.*
* Creating Python Virtual Environments
* Installing Python VS Code Extension
* Sample Flask Application
* Jinja Templating for Dynamic Web Pages
* Using pip to freeze Python dependencies
* Building the Docker image using Dockerfile
* Writing Docker Compose file
* Writing Kubernetes Manifest files for the application
* Creating Helm Chart

## Installation

Upgrade pip

```bash
pip install --upgrade pip
```

Install requirements

```bash
pip install -r flask-basics/requirements.txt
```

## Run application

Export environment variable

```bash
export FLASK_APP=flask-basics.src.app
```

Run Flask appplication

```bash
flask run
```

## Run application using Docker

```bash
docker build -t webapp:1.0 ./flask-basics
docker run -d -p 80:5000 --name web webapp:1.0
```

## Run application using Docker Compose

```bash
docker compose build
docker compose up -d
```

## Test the application

```bash
# Using local environment
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/details

# Using Docker
curl http://localhost/
curl http://localhost/health
curl http://localhost/details
```

## References

* [Install Docker on Debian](https://docs.docker.com/engine/install/debian/)
* [Install Kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
* [Minikube Start](https://minikube.sigs.k8s.io/docs/start/)
* [Microservices in Python using Flask Framework | Dockerize and Deploy to Kubernetes with Helm](https://www.youtube.com/watch?v=SdTzwYmsgoU)