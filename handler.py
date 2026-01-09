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
    except: pass
ensure_gpu()
# -------------------------------

def convert_to_wav_standard(input_path):
    """
    LA FONCTION SAUVEUR : 
    Elle prend un fichier (M4A, MP3, OGG...) et force sa conversion en WAV propre.
    """
    temp_wav = input_path + "_converted.wav"
    try:
        # On demande à FFMPEG de lire le fichier (peu importe son format réel)
        # et de le recracher en WAV Mono 44100Hz
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le",
            temp_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        shutil.move(temp_wav, input_path)
        print("✅ Fichier converti en WAV Standard (M4A corrigé).")
        return True
    except Exception as e:
        print(f"❌ Erreur conversion: {e}")
        return False

def download_file(url, target_path):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r, open(target_path, 'wb') as f: shutil.copyfileobj(r, f)
        return True
    except: return False

def download_model(url, name):
    target = os.path.join(CUSTOM_MODEL_DIR, name)
    if os.path.exists(target) and glob.glob(f"{target}/*.pth"): return True
    if os.path.exists(target): shutil.rmtree(target)
    os.makedirs(target, exist_ok=True)
    try:
        zip_p = os.path.join(target, "m.zip")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r, open(zip_p, 'wb') as f: shutil.copyfileobj(r, f)
        with zipfile.ZipFile(zip_p, 'r') as z: z.extractall(target)
        os.remove(zip_p)
        pth = glob.glob(f"{target}/**/*.pth", recursive=True)
        if pth: shutil.move(pth[0], os.path.join(target, os.path.basename(pth[0])))
        return True
    except: return False

def handler(job):
    job_input = job.get("input", {})
    
    # 1. On récupère URL ou Base64
    audio_url = job_input.get("audio_url")
    audio_base64 = job_input.get("audio_base64")
    
    model_name = job_input.get("model_name", "Eminem")
    model_url = job_input.get("model_url")
    
    # Paramètres (avec valeurs par défaut pour forcer l'accent)
    pitch = str(job_input.get("pitch", 0))
    f0 = job_input.get("f0_method", "rmvpe")
    # Index à 1 = Force l'accent du modèle à fond
    index = str(job_input.get("index_rate", 1)) 
    # Protect à 0 = Autorise l'IA à modifier la prononciation
    protect = str(job_input.get("protect", 0))  
    
    # Gestion Modèle
    if model_name != "Eminem" and not os.path.exists(os.path.join(CUSTOM_MODEL_DIR, model_name)):
        if model_url: download_model(model_url, model_name)

    # Préparation fichiers
    input_path = "/tmp/input_audio.wav" 
    output_dir = "/tmp/output_rvc"
    if os.path.exists(output_dir): shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(input_path): os.remove(input_path)

    # 2. Écriture du fichier brut (M4A ou autre)
    try:
        if audio_url:
            download_file(audio_url, input_path)
        elif audio_base64:
            with open(input_path, "wb") as f: f.write(base64.b64decode(audio_base64))
        else:
            return {"error": "Aucun audio"}

        # 3. LE CORRECTIF ULTIME : On force la conversion en WAV
        # C'est ici que ton M4A devient lisible par l'IA
        convert_to_wav_standard(input_path)

        # 4. Conversion RVC
        cmd = [
            "urvc", "generate", "convert-voice",
            input_path, output_dir, model_name,
            "--f0-method", f0,
            "--n-semitones", pitch,
            "--no-split-voice",       
            "--index-rate", index,     
            "--rms-mix-rate", "0.25", 
            "--protect-rate", protect
        ]
        
        print(f"Conversion: {model_name} (Pitch {pitch})...")
        subprocess.run(command, check=True)

        res = glob.glob(f"{output_dir}/*.wav")
        if not res: return {"error": "No output"}
        
        with open(res[0], "rb") as f:
            return {"status": "success", "audio_base64": base64.b64encode(f.read()).decode("utf-8")}

    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
