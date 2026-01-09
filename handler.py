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

def convert_to_wav_standard(input_path):
    """
    Transforme n'importe quel fichier (M4A, MP3, OGG, téléchargé ou non) en WAV Mono 44kHz.
    Indispensable pour que RVC ne rejette pas le fichier.
    """
    temp_wav = input_path + "_converted.wav"
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-ac", "1",                        # Force Mono
            "-ar", "44100",                    # Force 44.1kHz
            "-c:a", "pcm_s16le",               # Force WAV Standard
            temp_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        shutil.move(temp_wav, input_path)
        print("Audio normalisé en WAV standard.")
        return True
    except Exception as e:
        print(f"Erreur conversion audio: {e}")
        return False

def download_file(url, target_path):
    """Télécharge un fichier depuis une URL"""
    try:
        # User-Agent pour éviter d'être bloqué par certains serveurs (CDN, S3, etc)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(target_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        return True
    except Exception as e:
        print(f"Erreur téléchargement fichier audio: {e}")
        return False

def download_and_install_model(url, model_name):
    target_dir = os.path.join(CUSTOM_MODEL_DIR, model_name)
    if os.path.exists(target_dir) and glob.glob(f"{target_dir}/*.pth"):
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
        pth_files = glob.glob(f"{target_dir}/**/*.pth", recursive=True)
        if not pth_files: return False
        final_pth_path = os.path.join(target_dir, os.path.basename(pth_files[0]))
        if pth_files[0] != final_pth_path: shutil.move(pth_files[0], final_pth_path)
        return True
    except Exception as e:
        print(f"Erreur install modèle: {e}")
        return False

def handler(job):
    job_input = job.get("input", {})
    
    # --- RECUPERATION INTELLIGENTE DES PARAMETRES ---
    audio_url = job_input.get("audio_url")       # Priorité 1
    audio_base64 = job_input.get("audio_base64") # Priorité 2
    
    model_name = job_input.get("model_name", "Eminem")
    model_url = job_input.get("model_url")
    
    pitch_change = str(job_input.get("pitch", 0))           
    f0_method = job_input.get("f0_method", "rmvpe")         
    index_rate = str(job_input.get("index_rate", 0.75))     
    protect_rate = str(job_input.get("protect", 0.33))      

    # 1. Gestion du Modèle
    if model_name != "Eminem":
        if not os.path.exists(os.path.join(CUSTOM_MODEL_DIR, model_name)):
            if not model_url: return {"status": "error", "message": "URL modèle manquante"}
            if not download_and_install_model(model_url, model_name):
                return {"status": "error", "message": "Echec téléchargement modèle"}

    # 2. Préparation des chemins
    input_path = "/tmp/input_audio.wav" 
    output_dir = "/tmp/output_rvc"
    
    if os.path.exists(output_dir): shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(input_path): os.remove(input_path)

    # 3. Récupération de l'Audio (URL ou Base64)
    try:
        if audio_url:
            print(f"Téléchargement audio depuis URL: {audio_url}")
            if not download_file(audio_url, input_path):
                return {"status": "error", "message": "Impossible de télécharger l'audio depuis l'URL"}
        elif audio_base64:
            print("Décodage audio depuis Base64")
            with open(input_path, "wb") as f:
                f.write(base64.b64decode(audio_base64))
        else:
            return {"status": "error", "message": "Aucun audio fourni (ni audio_url, ni audio_base64)"}

        # --- ETAPE CRITIQUE : NETTOYAGE (M4A -> WAV) ---
        convert_to_wav_standard(input_path)
        # -----------------------------------------------

        # 4. Conversion RVC
        command = [
            "urvc", "generate", "convert-voice",
            input_path, output_dir, model_name,
            "--f0-method", f0_method,
            "--n-semitones", pitch_change,
            "--no-split-voice",       
            "--index-rate", index_rate,
            "--rms-mix-rate", "0.25", 
            "--protect-rate", protect_rate
        ]
        
        print(f"Conversion: {model_name} | Pitch: {pitch_change}")
        subprocess.run(command, check=True)

        # 5. Retour du résultat
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
        print(f"Erreur RVC: {e}")
        return {"status": "error", "message": "Erreur processus RVC"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

runpod.serverless.start({"handler": handler})
