FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential git ffmpeg curl wget libsndfile1 ca-certificates \
    zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev \
    libreadline-dev libffi-dev libsqlite3-dev libbz2-dev liblzma-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
RUN wget https://www.python.org/ftp/python/3.12.4/Python-3.12.4.tgz && \
    tar -xf Python-3.12.4.tgz && \
    cd Python-3.12.4 && \
    ./configure --enable-optimizations --with-ensurepip=install && \
    make -j $(nproc) && \
    make altinstall && \
    cd .. && rm -rf Python-3.12.4 Python-3.12.4.tgz
RUN ln -sf /usr/local/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip
RUN python --version && pip --version
RUN pip install "pip==23.3.1"
RUN pip install --no-cache-dir "setuptools<70" wheel ninja cython numpy
# NE PAS installer PyTorch manuellement - laisser ultimate-rvc le faire
RUN pip install runpod
# Ultimate RVC installera PyTorch avec la bonne version CUDA
RUN pip install "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu128
COPY handler.py /handler.py
CMD [ "python", "-u", "/handler.py" ]
