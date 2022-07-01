# WG Project

## Client

    TODO : python requirements
    TODO : dockerize the client

    cp .env.client.example .env.client
    bash scripts/run_client.sh to start the client

## Server

    TODO : dockerize flask

    install requirements with pip3 -r requirements.txt in server/wg folder
    cp .env.server.example .env.server

    IMPORTANT : to enable signup set DEVELOPMENT=1

    cp server/wg/db.sqlite.seed server/wg/db.sqlite
    bash scripts/run_redis.sh to start server
    bash scripts/run_server.sh to start flask

    IMPORTANT : after signup set DEVELOPMENT=0
    IMPORTANT : in production set FLASK_DEBUG=0
    
    


