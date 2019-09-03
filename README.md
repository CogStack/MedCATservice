# MedCAT Service API

It requires flask to be used, set it up by running:
```
export FLASK_ENV=development
export FLASK_APP=api.py

flask run --host <ip/host>
```


The api is available via:
```
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"text": "lung cancer diagnosis"}' \
  <ip/host>
```
