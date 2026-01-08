# 1. Image DEVEL pour avoir GCC/G++ (indispensable pour compiler Fairseq)
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# 2. Installation Système complète
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
    cmake && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. Pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# 4. Alias Python
RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip

# 5. Pré-requis de compilation
# On installe Cython et Numpy AVANT car Fairseq en a besoin pour se compiler
RUN pip install --no-cache-dir --upgrade pip setuptools wheel ninja cython numpy

# 6. INSTALLATION MANUELLE DE FAIRSEQ (Le Correctif)
# On récupère la version de développement qui est compatible Python 3.12+
# On ignore les erreurs de build isolation pour forcer l'usage de notre Numpy
RUN pip install --no-build-isolation git+https://github.com/facebookresearch/fairseq.git

# 7. Installation de Ultimate RVC
# On installe le reste. Si Fairseq est déjà là, il ne tentera pas de le réinstaller et ne plantera pas.
RUN pip install "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu121

# 8. SDK RunPod
RUN pip install runpod

# 9. Handler
COPY handler.py /handler.py

CMD [ "python", "-u", "/handler.py" ]
