#!/bin/bash

# Define default port values
ARANGO_PORT=6438
ARANGO_URL=http://localhost
BACKEND_PORT=5000
FRONTEND_PORT=8080
APP_URL=http://localhost


# Parse command line arguments to override default ports
while [[ $# -gt 0 ]]; do
    case "$1" in
        --backend-port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --app-url)
            APP_URL="$2"
            shift 2
            ;;
        #--arango-port)
        #    ARANGO_PORT="$2"
        #    shift 2
        #    ;;
        #--arango-url)
        #    ARANGO_URL="$2"
        #    shift 2
        #    ;;
        *)
            echo "Invalid argument: $1"
            exit 1
            ;;
    esac
done


# Update the .env file with the new port numbers
# increment ARANGO_PORT by 1 (offset) !!
echo "ARANGO_PORT=$(($ARANGO_PORT+1))" > frontend/.env
echo "ARANGO_URL=$ARANGO_URL" >> frontend/.env
echo "VUE_APP_BACKEND_PORT=$BACKEND_PORT" >> frontend/.env
echo "VUE_APP_FRONTEND_PORT=$FRONTEND_PORT" >> frontend/.env
echo "VUE_APP_URL=$APP_URL" >> frontend/.env


# Start ArangoDB locally with the specified port
cd arango_instance && arangodb --starter.mode=single --auth.jwt-secret=/etc/arangodb3/secret/arangodb.secret --starter.port "$ARANGO_PORT" &

# Wait for ArangoDB to start
sleep 5

# Switch to backend directory and start the backend server (assuming your command to start it is 'uvicorn app:app')
cd backend && 
uvicorn src.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &

# Start the npm development server for the Vue frontend
cd frontend && 
npm run serve -- --port "$FRONTEND_PORT"

# Cleanup: Kill ArangoDB and the backend server when the frontend server is terminated
trap "pkill -P $$ && kill -9 $$" EXIT

# Wait for all processes to finish
wait
