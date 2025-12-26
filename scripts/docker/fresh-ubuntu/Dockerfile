FROM ubuntu:latest

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y python3 python3-pip
COPY *.whl /
RUN pip install /*.whl --break-system-packages
