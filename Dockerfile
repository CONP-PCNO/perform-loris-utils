FROM centos:centos7

RUN yum install -y git && \
    curl -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    sh miniconda.sh -b -p /miniconda

ENV VIRTUAL_ENV "/miniconda"
ENV PATH "$VIRTUAL_ENV/bin:$PATH"

RUN python3 -m pip install requests && \
    conda install -y -c conda-forge git-annex && \
    git clone -n https://github.com/mathdugre/datalad-crawler.git /datalad-crawler

WORKDIR /datalad-crawler

RUN git checkout 73b15e6254ff0c6bfb01ae490d7c3cadb759c124 && \
    python -m pip install -e .

COPY src/ /app/src

WORKDIR /app

ENTRYPOINT ["/bin/bash", "/app/src/run.sh"]

