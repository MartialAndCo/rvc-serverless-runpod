# 1. Image DEVEL (Base solide)
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
# 2. Système & Python 3.11 (plus stable, pas besoin de PPA)
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
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# 3. Alias Python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3
# 4. Upgrade pip
RUN python -m pip install --upgrade pip
# 5. Downgrade PIP (Vital pour Fairseq)
RUN python -m pip install "pip==23.3.1"
# 6. Outils de Build
RUN pip install --no-cache-dir "setuptools<70" wheel ninja cython numpy
# 7. PYTORCH
RUN pip install --no-cache-dir torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121
# 8. Fairseq (Build from Source)
RUN pip install --no-build-isolation git+https://github.com/facebookresearch/fairseq.git
# 9. SDK RunPod
RUN pip install runpod
# 10. Ultimate RVC
RUN pip install "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu121
# 11. Handler
COPY handler.py /handler.py
CMD [ "python", "-u", "/handler.py" ]
