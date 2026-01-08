# 1. Image de base NVIDIA (Compatible RunPod)
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Désactiver les interactions (timezone, etc)
ENV DEBIAN_FRONTEND=noninteractive

# 2. Préparer le système : Installer les certificats et outils de base AVANT le PPA
# On sépare les étapes pour éviter que tout plante d'un coup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    gnupg \
    software-properties-common \
    wget \
    curl \
    git \
    ffmpeg \
    build-essential

# 3. Ajouter le dépôt Python 3.12 (deadsnakes)
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update

# 4. Installer Python 3.12 et ses modules
RUN apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3.12-distutils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 5. Installer PIP pour Python 3.12 (via script officiel pour éviter les conflits apt)
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# 6. Créer les alias (python -> python3.12)
RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip

# 7. Installer le SDK RunPod
RUN pip install runpod

# 8. Installer Ultimate RVC
# On force l'index-url pour s'assurer d'avoir les versions compatibles CUDA
RUN pip install --no-cache-dir "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu121

# 9. Copier le worker
COPY handler.py /handler.py

# 10. Lancer
CMD [ "python", "-u", "/handler.py" ]
