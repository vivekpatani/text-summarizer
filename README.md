# Python Wrapper Around CoreNLP along with Text Summarizer
This is a simple text summarizer using a sentencer, depenency parser and reconstructor.  

## Stack Used
- Python 3.5
- Docker
- MariaDB

## Prerequisites - Please follow instructions
- Install MariaDB - https://downloads.mariadb.org/
- Install MySQL Connector - https://dev.mysql.com/downloads/connector/python/
- Install Python 3.5+

### For Windows (Untested)
- Install Docker - https://docs.docker.com/docker-for-windows/install/
- Download Stanford CoreNLP - http://nlp.stanford.edu/software/stanford-corenlp-full-2016-10-31.zip
- Move it to the folder ```corenlp-server``` and extract it.
- Using powershell from Project Root - ```cd corenlp-server``` and Execute ```docker build -t corenlp-server .```
- This ensures that the docker container is now created.

### For MacOS
- Install Docker - https://docs.docker.com/docker-for-mac/
- From Project Root - ```cd corenlp-server``` and get Stanford CoreNLP Server by executing- ```./get-corenlp.sh```
- From Project Root - ```cd corenlp-server``` and Execute ```docker build -t corenlp-server .```
- This ensures that the docker container is now created.

### For Linux (Tested on Ubuntu only)
- From Project Root - ```cd corenlp-server``` and get Stanford CoreNLP Server by executing - ```./get-corenlp.sh```
- Docker - ```curl -sSL https://get.docker.com/ | sh -y```
- Give docker local user rights - ```sudo usermod -aG docker $USER```
- Reboot Computer
- From Project Root - ```cd corenlp-server``` and Execute ```docker build -t corenlp-server .```
- This ensures that the docker container is now created.

## One Time Setup
- Rename **config-sample.json** to **config.json**
- Change the configuration for MariaDB as per your computer
- Create a new database (by default it is called text_summarization).
- If you for some reason change the default name, change it in script.py as well.

## How to initiate server
- From Project Root - ```python init-server.py```

## How to Terminate Server
- From Project Root - ```python terminate-server.py```

## Usage
- First Initialize Server.
- Please Edit script.py according to your requirements:  
	- Execute - ```script.py``` to give it a run.
	- To change input, edit ```input/input.txt```
- Once done with summarization make sure to terminate server.

## For errors
- Check **output.log**

## Todo
- Stats
- Templating

## Tested on
- Elementary OS (Ubuntu 16.04.02)

## Quirks
- If for some reason Docker container acts weird **Terminate Server and Reinitialise it!**

## Acknowledgements
- https://github.com/hotpxl/corenlp-server for Docker container setup and download script.