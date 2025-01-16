# Overview
The repository is modularised into three main components:
- model_code: Contains the base model code such as KNN and LR for training models
- visualisation_code: Contains code for visualising suggestions
- web_code: Contains starter code for a interactive web implementation (development has been paused)
- message_advisor_code: Contains client code for Elastic Search vector database for querying message advice given game state

## Setup
Perform the following setup to run the code.
- All setup steps should be completed from the topmost directory
- Using a venv is recommended

Install packages in requirements.txt to build the model with the correct version:
- pip install -r requirements.txt

To make code imports cleaner across multiple directories, packages were used in conjunction with setuptools. To create the package:
- pip install -e .

# Usage
## model_code/predict.py
Renders predictions from the model on a test set
Keyword arguments:
- -t:   The path to the jsonl files containing the test states of the model
- -m:   The path to the model folder containing the model binaries
- -o:   The path to the output folder for the rendered suggestions overlayed on the map
- -g:   The max number of games to render from the test file (-1 for full file)
- -p:   The max number of phases to render for any game (-1 for full game)
- -u:   The max number of units to render suggestions for any phase (-1 for all units)
- -s:   The max number of order suggestions to render for any unit (-1 for all suggestions)

## visualisation_code/render_examples.py
Renders example suggestions on states defined in "examples.py"
Keyword arguments:
- -o:   The path to the output folder for the rendered suggestions overlayed on the map

## message_advisor_code/create_index.py
Create and populate elastic search index for querying message advice

The script requires a running elastic search instance.
To start a local ES single-node cluster using docker:
```bash
$ docker pull docker.elastic.co/elasticsearch/elasticsearch:8.16.1
$ docker run --name es01 --net elastic -p 9200:9200 -it -m 1GB docker.elastic.co/elasticsearch/elasticsearch:8.16.1
```

The above command will generate a password for the elastic user. Set ELASTIC_PASSWORD in the script with this password.

Additionally, an SSL certificate is also generated, which can be copied to the local machine:
```bash
$ docker cp es01:/usr/share/elasticsearch/config/certs/http_ca.crt .
```
Set CERT_PATH to be the downloaded certificate path

Make REST API call to test if the container is running:
```bash
$ curl --cacert http_ca.crt -u elastic:$ELASTIC_PASSWORD https://localhost:9200
```

The dataset for populating the index can be downloaded ['here'](https://unisydneyedu-my.sharepoint.com/my?id=%2Fpersonal%2Fnhad0493%5Funi%5Fsydney%5Fedu%5Fau%2FDocuments%2FDARPA%20files)