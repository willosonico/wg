if [ -f .env.client ]; then
  export $(echo $(cat .env.client | sed 's/#.*//g'| xargs) | envsubst)
fi
python3 client/main.py