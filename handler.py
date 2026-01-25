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

# --- ZONE AUTO-REPARATION GPU ---
def ensure_gpu():
    try:
        import onnxruntime
        if 'CUDAExecutionProvider' not in onnxruntime.get_available_providers():
            print("⚠️ CPU détecté. Réparation GPU en cours...")
            subprocess.run("pip uninstall -y onnxruntime onnxruntime-gpu", shell=True)
            subprocess.run("pip install onnxruntime-gpu", shell=True)
    except: 
        pass

ensure_gpu()
# -------------------------------

def download_file(url, target_path):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r, open(target_path, 'wb') as f:
            shutil.copyfileobj(r, f)
        return True
    except:
        return False

def download_model(url, name):
    target = os.path.join(CUSTOM_MODEL_DIR, name)
    if os.path.exists(target) and glob.glob(f"{target}/*.pth"):
        return True
    if os.path.exists(target):
        shutil.rmtree(target)
    os.makedirs(target, exist_ok=True)
    try:
        zip_p = os.path.join(target, "m.zip")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r, open(zip_p, 'wb') as f:
            shutil.copyfileobj(r, f)
        with zipfile.ZipFile(zip_p, 'r') as z:
            z.extractall(target)
        os.remove(zip_p)
        pth = glob.glob(f"{target}/**/*.pth", recursive=True)
        if pth:
            shutil.move(pth[0], os.path.join(target, os.path.basename(pth[0])))
        return True
    except:
        return False

def handler(job):
    job_input = job.get("input", {})
    
    # 1. Récupération audio URL ou Base64
    audio_url = job_input.get("audio_url")
    audio_base64 = job_input.get("audio_base64")
    
    model_name = job_input.get("model_name", "Eminem")
    model_url = job_input.get("model_url")
    
    # Paramètres RVC
    pitch = str(job_input.get("pitch", 0))
    f0 = job_input.get("f0_method", "rmvpe")
    index = str(job_input.get("index_rate", 0.6))
    protect = str(job_input.get("protect", 0.33))
    rms_mix = str(job_input.get("rms_mix_rate", 0.25))
    clean_strength = str(job_input.get("clean_strength", 0.5))  # ← NOUVEAU
    
    # Gestion modèle custom
    if model_name != "Eminem" and not os.path.exists(os.path.join(CUSTOM_MODEL_DIR, model_name)):
        if model_url:
            download_model(model_url, model_name)

    # Préparation fichiers
    input_path = "/tmp/input_audio.wav"
    output_dir = "/tmp/output_rvc"
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    if os.path.exists(input_path):
        os.remove(input_path)

    # 2. Écriture du fichier audio
    try:
        if audio_url:
            download_file(audio_url, input_path)
        elif audio_base64:
            with open(input_path, "wb") as f:
                f.write(base64.b64decode(audio_base64))
        else:
            return {"error": "Aucun audio fourni (audio_url ou audio_base64 requis)"}

        # 3. Conversion RVC (COMMANDE CORRIGÉE)
        cmd = [
            "urvc", "generate", "convert-voice",  # ← CHANGÉ : ajout de "cli"
            input_path, output_dir, model_name,
            "--f0-method", f0,
            "--n-semitones", pitch,
            "--no-split-voice",
            "--index-rate", index,
            "--rms-mix-rate", rms_mix,
            "--protect-rate", protect,
            "--clean-voice",                    # ← NOUVEAU : remplace filter-radius
            "--clean-strength", clean_strength  # ← NOUVEAU : réduit les artefacts
        ]
        
        print(f"🎤 Conversion: {model_name} (Pitch {pitch}, Clean {clean_strength})...")
        subprocess.run(cmd, check=True)

        # 4. Récupération résultat
        res = glob.glob(f"{output_dir}/*.wav")
        if not res:
            return {"error": "Aucun fichier de sortie généré"}
        
        with open(res[0], "rb") as f:
            return {
                "status": "success",
                "audio_base64": base64.b64encode(f.read()).decode("utf-8")
            }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Démarrage du worker RunPod
runpod.serverless.start({"handler": handler})
