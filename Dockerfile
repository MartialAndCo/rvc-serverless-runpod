# 1. On utilise l'image DEVEL et pas RUNTIME.
# C'est CRUCIAL car RVC doit compiler des modules (Fairseq, etc.) lors de l'installation.
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Configuration pour éviter les questions lors de l'installation
ENV DEBIAN_FRONTEND=noninteractive

# 2. Installation des outils système + Python 3.12
# J'ai retiré 'python3.12-distutils' qui causait l'erreur 100 car il n'existe plus.
# J'ai ajouté 'libsndfile1' qui est indispensable pour le traitement audio (souvent oublié).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    build-essential \
    git \
    ffmpeg \
    curl \
    libsndfile1 \
    ca-certificates \
    gnupg && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. Installation de PIP pour Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# 4. Alias pour forcer l'usage de Python 3.12 par défaut
RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip

# 5. Mise à jour des outils de build (Setuptools remplace distutils)
RUN pip install --upgrade pip setuptools wheel

# 6. Installation du SDK RunPod
RUN pip install runpod

# 7. Installation de Ultimate RVC
# On installe d'abord numpy/cython pour aider la compilation de Fairseq si nécessaire
RUN pip install numpy cython
RUN pip install --no-cache-dir "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu121

# 8. Ajout du handler
COPY handler.py /handler.py

# 9. Démarrage
CMD [ "python", "-u", "/handler.py" ]
