FROM ubuntu:xenial
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections && \
    apt-get update --yes && \
    apt-get install --yes software-properties-common && \
    apt-get update --yes && \
    apt-get install --yes build-essential openjdk-8-jdk python python-dev && \
    apt-get dist-upgrade --yes
COPY ./stanford-corenlp-full-2016-10-31 /corenlp-server
WORKDIR /corenlp-server

EXPOSE 80
CMD java -mx8g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer --port 80 --timeout 50000