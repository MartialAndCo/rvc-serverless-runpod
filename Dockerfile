# 1. Image DEVEL (contient GCC/G++ nécessaires pour compiler les dépendances audio)
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# 2. Installation Système & Python 3.12
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    build-essential \
    ninja-build \
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

# 3. Installation de PIP
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# 4. Alias Python
RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip

# 5. Pré-installation critiques (La clé du succès est ici)
# On installe setuptools<70 car les versions récentes cassent la compilation de certains vieux modules audio.
# On installe wheel, ninja, cython et numpy AVANT tout le reste.
RUN pip install --no-cache-dir --upgrade pip "setuptools<70" wheel ninja cython numpy

# 6. Installation de PyTorch MANUELLE (Avant RVC)
# Cela garantit que les headers Torch sont présents quand RVC en aura besoin.
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 7. Installation de RunPod SDK
RUN pip install runpod

# 8. Installation de Ultimate RVC
# On utilise --no-build-isolation pour forcer l'utilisation de nos paquets (Torch/Numpy) pré-installés
RUN pip install --no-cache-dir "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu121

# 9. Copie du handler
COPY handler.py /handler.py

# 10. Démarrage
CMD [ "python", "-u", "/handler.py" ]
