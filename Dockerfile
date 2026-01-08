# 1. Image DEVEL (Indispensable pour la compilation)
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
# Ajout des chemins CUDA pour la compilation
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# 2. Installation Système & Python 3.12
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

# 3. Pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# 4. Alias Python
RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip

# 5. Outils de Build & Compatibilité
# IMPORTANT : On bloque setuptools sous la version 70 car la version 80 casse Fairseq
RUN pip install --no-cache-dir --upgrade pip "setuptools<70" wheel ninja cython numpy

# 6. INSTALLATION DE PYTORCH (L'étape manquante)
# Fairseq a besoin que Torch soit DÉJÀ là pour s'installer
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 7. Installation de Fairseq (Build from Source)
# Maintenant que Torch est là, ça ne plantera plus.
RUN pip install --no-build-isolation git+https://github.com/facebookresearch/fairseq.git

# 8. RunPod SDK
RUN pip install runpod

# 9. Ultimate RVC
# On installe le reste sans casser ce qu'on a déjà fait
RUN pip install "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu121

# 10. Handler
COPY handler.py /handler.py

CMD [ "python", "-u", "/handler.py" ]
