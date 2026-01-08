import runpod
import subprocess
import os
import base64
import glob
import shutil
import urllib.request
import zipfile

# Dossier des modèles
CUSTOM_MODEL_DIR = "/tmp/voice_models"
os.environ["URVC_VOICE_MODELS_DIR"] = CUSTOM_MODEL_DIR

def download_and_install_model(url, model_name):
    """Télécharge et installe le modèle proprement"""
    target_dir = os.path.join(CUSTOM_MODEL_DIR, model_name)
    # Vérification cache
    if os.path.exists(target_dir) and glob.glob(f"{target_dir}/*.pth"):
        print(f"Modèle '{model_name}' déjà présent.")
        return True

    print(f"Installation du modèle '{model_name}'...")
    if os.path.exists(target_dir): shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    
    zip_path = os.path.join(target_dir, "model.zip")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        
        os.remove(zip_path)
        
        # On s'assure que le .pth est bien visible à la racine du dossier du modèle
        pth_files = glob.glob(f"{target_dir}/**/*.pth", recursive=True)
        if not pth_files: return False
            
        final_pth_path = os.path.join(target_dir, os.path.basename(pth_files[0]))
        if pth_files[0] != final_pth_path:
            shutil.move(pth_files[0], final_pth_path)
            
        return True
    except Exception as e:
        print(f"Erreur install: {e}")
        return False

def handler(job):
    job_input = job.get("input", {})
    
    # --- RECUPERATION DES PARAMETRES ---
    audio_base64_input = job_input.get("audio_base64")
    model_name = job_input.get("model_name", "Eminem")
    model_url = job_input.get("model_url")
    
    # Réglages audio fins
    pitch_change = str(job_input.get("pitch", 0))          
    f0_method = job_input.get("f0_method", "crepe")        
    index_rate = str(job_input.get("index_rate", 0.75))    
    protect_rate = str(job_input.get("protect", 0.33))     

    if not audio_base64_input:
        return {"status": "error", "message": "Audio manquant"}

    # 1. Installation Modèle
    if model_name != "Eminem":
        if not os.path.exists(os.path.join(CUSTOM_MODEL_DIR, model_name)):
            if not model_url:
                return {"status": "error", "message": "URL modèle manquante pour première installation"}
            if not download_and_install_model(model_url, model_name):
                return {"status": "error", "message": "Echec téléchargement modèle"}

    # 2. Nettoyage et Préparation
    input_path = "/tmp/input_audio.wav" 
    output_dir = "/tmp/output_rvc"
    
    if os.path.exists(output_dir): shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(input_path): os.remove(input_path)

    try:
        # 3. Ecriture fichier
        with open(input_path, "wb") as f:
            f.write(base64.b64decode(audio_base64_input))

        # 4. Commande RVC (CORRIGÉE : --filter-radius supprimé)
        command = [
            "urvc", "generate", "convert-voice",
            input_path,
            output_dir,
            model_name,
            "--f0-method", f0_method,
            "--n-semitones", pitch_change,
            "--no-split-voice",       
            "--index-rate", index_rate,
            # "--filter-radius" SUPPRIMÉ CAR NON SUPPORTÉ
            "--rms-mix-rate", "0.25", 
            "--protect-rate", protect_rate
        ]
        
        print(f"Lancement conversion: {model_name} | Pitch: {pitch_change} | Algo: {f0_method}")
        subprocess.run(command, check=True)

        # 5. Encodage retour
        output_files = glob.glob(f"{output_dir}/*.wav")
        if not output_files: return {"status": "error", "message": "Pas de fichier généré"}
        
        with open(output_files[0], "rb") as audio_file:
            audio_encoded = base64.b64encode(audio_file.read()).decode("utf-8")

        return {
            "status": "success",
            "model": model_name,
            "audio_base64": audio_encoded
        }

    except subprocess.CalledProcessError as e:
        # On capture l'erreur de commande pour voir les logs
        print(f"Erreur RVC CLI: {e}")
        return {"status": "error", "message": "Erreur commande RVC (voir logs)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

runpod.serverless.start({"handler": handler})
