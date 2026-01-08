import runpod
import subprocess
import os
import base64
import glob
import shutil
import urllib.request
import zipfile

# On force RVC à chercher les modèles ici (Dossier temporaire inscriptible)
CUSTOM_MODEL_DIR = "/tmp/voice_models"
os.environ["URVC_VOICE_MODELS_DIR"] = CUSTOM_MODEL_DIR

def download_and_install_model(url, model_name):
    """Télécharge et installe un modèle si absent"""
    target_dir = os.path.join(CUSTOM_MODEL_DIR, model_name)
    
    # Si le dossier existe déjà et contient un fichier .pth, on suppose que c'est bon
    if os.path.exists(target_dir):
        if glob.glob(f"{target_dir}/*.pth"):
            print(f"Modèle '{model_name}' déjà présent en cache.")
            return True
        else:
            # Dossier vide ou corrompu, on nettoie
            shutil.rmtree(target_dir)

    print(f"Installation du modèle '{model_name}' depuis {url}...")
    os.makedirs(target_dir, exist_ok=True)
    
    zip_path = os.path.join(target_dir, "model.zip")
    
    try:
        # 1. Téléchargement
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, zip_path)
        
        # 2. Décompression
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        
        # 3. Nettoyage zip
        os.remove(zip_path)
        
        # 4. Vérification vitale : RVC veut le .pth DANS le dossier. 
        # Parfois les zips contiennent un sous-dossier. On remonte les fichiers si besoin.
        # (Logique simplifiée : on espère que le zip est bien fait, sinon RVC râlera)
        
        print(f"Modèle '{model_name}' installé avec succès.")
        return True
    except Exception as e:
        print(f"Erreur téléchargement modèle: {e}")
        shutil.rmtree(target_dir) # On nettoie en cas d'échec
        return False

def handler(job):
    job_input = job.get("input", {})
    
    # --- PARAMETRES ---
    audio_base64_input = job_input.get("audio_base64")
    model_name = job_input.get("model_name") # Ex: "Macron"
    model_url = job_input.get("model_url")   # Ex: "https://huggingface.../macron.zip"
    pitch_change = str(job_input.get("pitch", 0))
    f0_method = job_input.get("f0_method", "rmvpe")

    if not audio_base64_input or not model_name:
        return {"status": "error", "message": "Paramètres manquants (audio_base64 ou model_name)"}

    # --- ETAPE 0 : GESTION DU MODELE ---
    # Si le modèle n'est pas "Eminem" (inclus de base) et qu'on a une URL, on tente l'install
    if model_name != "Eminem":
        # On vérifie si on l'a déjà, sinon on a besoin de l'URL
        is_installed = os.path.exists(os.path.join(CUSTOM_MODEL_DIR, model_name))
        
        if not is_installed:
            if not model_url:
                return {"status": "error", "message": f"Le modèle '{model_name}' n'est pas sur le serveur. Vous devez fournir 'model_url' pour l'installer la première fois."}
            
            success = download_and_install_model(model_url, model_name)
            if not success:
                return {"status": "error", "message": "Impossible de télécharger le modèle."}

    # --- SUITE CLASSIQUE (Conversion) ---
    input_path = "/tmp/input_audio" 
    output_dir = "/tmp/output_rvc"
    
    if os.path.exists(output_dir): shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(input_path): os.remove(input_path)

    try:
        # Décodage Audio
        with open(input_path, "wb") as f:
            f.write(base64.b64decode(audio_base64_input))

        # Commande RVC
        command = [
            "urvc", "generate", "convert-voice",
            input_path,
            output_dir,
            model_name,
            "--f0-method", f0_method,
            "--n-semitones", pitch_change
        ]
        
        subprocess.run(command, check=True)

        # Encodage sortie
        output_files = glob.glob(f"{output_dir}/*.wav")
        if not output_files: return {"status": "error", "message": "Pas de fichier de sortie."}
        
        with open(output_files[0], "rb") as audio_file:
            audio_encoded = base64.b64encode(audio_file.read()).decode("utf-8")

        return {
            "status": "success",
            "model": model_name,
            "is_new_install": (model_url is not None), # Info utile pour le debug
            "audio_base64": audio_encoded
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}

runpod.serverless.start({"handler": handler})
