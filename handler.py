# 1. Image DEVEL
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
# 2. Système + Python 3.12 (CACHE BUST: 20260115-2237)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    build-essential \
    git \
    ffmpeg \
    curl \
    libsndfile1 \
    ca-certificates \
    gnupg \
    cmake \
    ninja-build \
    gpg-agent && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776 && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# 3. Pip Bootstrap
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12
# 4. Downgrade PIP
RUN python3.12 -m pip install "pip==23.3.1"
# 5. Alias
RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip
# 6. Vérif Python (debug)
RUN python --version && pip --version
# 7. Outils de Build
RUN pip install --no-cache-dir "setuptools<70" wheel ninja cython numpy
# 8. PYTORCH cu121
RUN pip install --no-cache-dir torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121
# 9. Fairseq
RUN pip install --no-build-isolation git+https://github.com/facebookresearch/fairseq.git
# 10. SDK RunPod
RUN pip install runpod
# 11. Ultimate RVC (depuis GitHub)
RUN pip install git+https://github.com/JackismyShephard/ultimate-rvc.git --extra-index-url https://download.pytorch.org/whl/cu121
# 12. Handler
COPY handler.py /handler.py
CMD [ "python", "-u", "/handler.py" ]
