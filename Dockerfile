# 1. Image DEVEL
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# 2. Système & Python 3.12
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
    ninja-build && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. Installation de PIP (bootstrap)
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# 4. CRITIQUE : DOWNGRADE PIP
# On installe pip 23.3.1 car les versions >24.1 rejettent les métadonnées invalides de omegaconf (requis par Fairseq)
RUN python3.12 -m pip install "pip==23.3.1"

# 5. Alias Python
RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip

# 6. Outils de Build
# Note : On ne met PAS à jour pip ici pour garder la version 23.3.1
RUN pip install --no-cache-dir "setuptools<70" wheel ninja cython numpy

# 7. PyTorch (Avant Fairseq)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 8. Fairseq (Build from Source)
# Avec pip 23.3.1, l'erreur "ResolutionImpossible" due au metadata disparaîtra
RUN pip install --no-build-isolation git+https://github.com/facebookresearch/fairseq.git

# 9. SDK RunPod
RUN pip install runpod

# 10. Ultimate RVC
RUN pip install "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu121

# 11. Handler
COPY handler.py /handler.py

CMD [ "python", "-u", "/handler.py" ]
