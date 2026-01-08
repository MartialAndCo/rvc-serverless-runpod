# 1. Utiliser une image de base NVIDIA avec CUDA 12.1 (Compatible RunPod et PyTorch moderne)
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Éviter les questions interactives lors de l'installation (Timezone, etc.)
ENV DEBIAN_FRONTEND=noninteractive

# 2. Mettre à jour et installer les outils système nécessaires
# On ajoute le PPA deadsnakes pour obtenir Python 3.12
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3.12-distutils \
    git \
    ffmpeg \
    curl \
    build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. Installer pip pour Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# 4. Créer des alias pour que "python" et "pip" pointent vers la version 3.12
RUN ln -s /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip

# 5. Installer le SDK RunPod (nécessaire car on n'utilise plus l'image de base runpod)
RUN pip install runpod

# 6. Installer Ultimate RVC
# Note : On pointe vers cu121 pour correspondre à notre image Docker CUDA 12.1
RUN pip install --no-cache-dir "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu121

# 7. Copier le script handler
COPY handler.py /handler.py

# 8. Démarrage
CMD [ "python", "-u", "/handler.py" ]
