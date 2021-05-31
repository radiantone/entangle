#FROM nvidia/cuda:11.3.0-devel-ubuntu20.04
FROM nvidia/cuda:11.0-base
RUN apt-get update && \
    apt-get install -y --no-install-recommends -y \
    python3.8 python3-pip python3.8-dev

RUN apt install -y wget 
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN mkdir /root/.conda 
RUN bash Miniconda3-latest-Linux-x86_64.sh -b
RUN rm -f Miniconda3-latest-Linux-x86_64.sh 

#RUN pip install virtualenv
#UN virtualenv --python=python3.8 venv
#RUN venv/bin/pip install py-entangle
#RUN venv/bin/pip install numba
ENV PATH="/root/miniconda3/bin:${PATH}"
RUN conda install cudatoolkit
RUN conda install numba
RUN pip install py-entangle
RUN conda --version
RUN which conda
ENTRYPOINT [ "bash" ]