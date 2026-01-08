# Image de base optimisée pour RunPod (déjà en cache souvent)
FROM runpod/base:0.4.0-cuda11.8.0

# Installation des dépendances système
USER root
RUN apt-get update && apt-get install -y ffmpeg git

# Installation de Python 3.10 (si pas présent) ou utilisation du venv existant
# Installation de Ultimate RVC
# Note: On utilise pip avec cache pour accélérer
RUN pip install --no-cache-dir "ultimate-rvc[cuda]" --extra-index-url https://download.pytorch.org/whl/cu128

# Copie du worker (handler)
COPY handler.py /handler.py

# Démarrage
CMD [ "python", "-u", "/handler.py" ]
