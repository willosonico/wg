if [ -f .env.server ]; then
  export $(echo $(cat .env.server | sed 's/#.*//g'| xargs) | envsubst)
fi
cd server
python3 -m flask run --host=0.0.0.0 --port=5000