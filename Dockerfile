# 1. Image DEVEL (Base solide)
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

# 3. Pip Bootstrap
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# 4. Downgrade PIP (Vital pour Fairseq)
RUN python3.12 -m pip install "pip==23.3.1"

# 5. Alias
RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip

# 6. Outils de Build
# On garde setuptools<70 pour la compatibilité
RUN pip install --no-cache-dir "setuptools<70" wheel ninja cython numpy

# 7. PYTORCH (CORRECTION ICI)
# On installe la version 'cu128' (CUDA 12.8) pour satisfaire Ultimate RVC.
# On ne met pas de version fixe, on laisse pip prendre la dernière dispo sur ce dépôt.
RUN pip install --no-cache-dir torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu128

# 8. Fairseq (Build from Source)
# Il va utiliser le Torch cu128 qu'on vient d'installer.
RUN pip install --no-build-isolation git+https://github.com/facebookresearch/fairseq.git

# 9. SDK RunPod
RUN pip install runpod

# 10. Ultimate RVC
# L'index URL correspond maintenant à ce qu'on a installé (cu128).
RUN pip install "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu128

# 11. Handler
COPY handler.py /handler.py

CMD [ "python", "-u", "/handler.py" ]
