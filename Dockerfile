FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y --no-install-recommends -y \
    python3.8 python3-pip python3.8-dev
    
RUN pip install virtualenv
RUN virtualenv --python=python3.8 venv
RUN venv/bin/pip install py-entangle
ENV PATH="venv/bin/:${PATH}"

ENTRYPOINT [ "bash" ]