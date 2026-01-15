# 1. NVIDIA CUDA Base
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
# 2. Dépendances système + build Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    curl \
    wget \
    libsndfile1 \
    ca-certificates \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libreadline-dev \
    libffi-dev \
    libsqlite3-dev \
    libbz2-dev \
    liblzma-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# 3. Compiler Python 3.12 depuis les sources
RUN wget https://www.python.org/ftp/python/3.12.4/Python-3.12.4.tgz && \
    tar -xf Python-3.12.4.tgz && \
    cd Python-3.12.4 && \
    ./configure --enable-optimizations --with-ensurepip=install && \
    make -j $(nproc) && \
    make altinstall && \
    cd .. && \
    rm -rf Python-3.12.4 Python-3.12.4.tgz
# 4. Alias Python
RUN ln -sf /usr/local/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip
# 5. Vérification
RUN python --version && pip --version
# 6. Downgrade PIP
RUN pip install "pip==23.3.1"
# 7. Outils de Build
RUN pip install --no-cache-dir "setuptools<70" wheel ninja cython numpy
# 8. PyTorch CUDA 12.1
RUN pip install --no-cache-dir torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121
# 9. Fairseq
RUN pip install --no-build-isolation git+https://github.com/facebookresearch/fairseq.git
# 10. SDK RunPod
RUN pip install runpod
# 11. Ultimate RVC
RUN pip install "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu121
# 12. Handler
COPY handler.py /handler.py
CMD [ "python", "-u", "/handler.py" ]
