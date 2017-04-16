# Python Wrapper Around CoreNLP along with Text Summarizer
This is a simple text summarizer using a sentencer, depenency parser and reconstructor.  

## Stack Used
- Python 3.5  
- Stanford Dependency Parser (Used as a backgroud daemon)
- Docker

## Prerequisites - Please follow instructions
- From Project Root - ```cd corenlp-server``` and get Stanford CoreNLP Server by executing - ```./get-corenlp.sh```
- Docker - ```curl -sSL https://get.docker.com/ | sh -y```
- Give docker local user rights - ```sudo usermod -aG docker $USER```
- Reboot Computer
- From Project Root - ```cd corenlp-server``` and Execute ```docker build -t corenlp-server .```
- If not installed, install Python 3.5

## How to initiate server
- From Project Root - ```python init-server.py```

## How to Terminate Server
- From Project Root - ```python terminate-server.py```

## Usage
Please Edit script.py according to your requirements:  
- Execute - ```script.py``` to give it a run.
- To change input, edit ```input/input.txt```

## Todo
- Extract Relations
- Implement a triple store
- Reconstruct sentences

## Acknowledgements
- https://github.com/hotpxl/corenlp-server for Docker container setup and download script.

## Tested on
- Elementary OS (Ubuntu 16.04.02)