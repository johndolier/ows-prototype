# README


## Dependencies 
Docker ( >= 3.0)

## Getting Started

- Clone the project from Github
- Move data and config files into the correct directories (see below)
- (Optional) Set the ports (see below)
- Start Docker
- Run <code> docker compose up </code>

The frontend will be available at <code> localhost:8080 </code>. 

*Note: When starting the service for the first time, the ArangoDB database gets initialized with all files, which can take a few minutes. If everything works correctly, next time you start the service, ArangoDB is already initialized by using the docker volume (arangodb-vol).*

### Ports and networking information
The docker compose command builds 3 containers which are connected with a Docker bridge (*ows-network*). Therefore, the containers can access the other containers via the docker network by **http://\<container-name\>:port**. 

For example, by default, ArangoDB listens to port 8529. Therefore, any container that is connected to *ows-network* can access the ArangoDB service with **http://arango-container:8529**. 


For debugging reasons, some of the ports are also exposed in the host network. 
- **http://localhost:6439** (ArangoDB server)
- **http://localhost:5000** (Backend API)
- **http://localhost:8080** (Frontend Web server)

If for some reason you want to change some of the ports, you can do this in the *docker-compose.yml* file. Please adapt *backend/src/config.yml* as well as the variable **BACKEND_URL** in *frontend/src/main.js* accordingly. 

### Folder structure
In order to build the application, you need to move both *config.yml* and the data (*arangodump*) inside the right folders before building the application with Docker. 


~~~
ows-prototype
|
|___frontend
|   |
|   |...
|
|___backend
|   |
|   |___src
|   |   |
|   |   |___config.yml
|   |   |
|   |   |___...
|   |
|   |___database
|       |
|       |____Database.py
|       |
|       |____EOGraphCreator.py
|       |
|       |____arangodump
|            |
|            |___nodes
|            |
|            |___edges
|
|__docker-compose.yml
|__README.md
~~~

***
***


# README (outdated!)
## Getting started (old)

Create conda environment 
<code>
  conda env create -f environment.yml
  conda activate prototype_env
</code>

After activating the conda environment, download the spacy component 
<code>
  python -m spacy download en_core_web_sm
</code>

## Set ports and URL
In the .env file, you can set the port numbers for the server and backend API, as well as the hosting URL (usually localhost). 

### Frontend

To set up the frontend, you first have to install the node modules 
<code>
  cd frontend // change to frontend working directory
  npm install // install the node dependencies
</code>


After installing the dependencies, the development server can be started with 
<code>
  npm run serve
</code>


### Backend
To start an instance for the backend FAST API server, use
<code>
  cd backend // change to backend working directory
  uvicorn src.main:app --host 0.0.0.0 --port 5000
</code>



After setting up both server instances, the web application can be accessed on "http://localhost:8080/". 


