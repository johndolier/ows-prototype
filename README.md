# README

## Note
This repository is currently in transition and migrating from Gitlab@DLR

## Set up environment

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


