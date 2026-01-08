import runpod
import subprocess
import os
import base64
import glob
import shutil

def handler(job):
    job_input = job.get("input", {})
    
    # 1. Récupération de l'input
    audio_base64_input = job_input.get("audio_base64")
    model_name = job_input.get("model_name", "Eminem")
    pitch_change = str(job_input.get("pitch", 0))
    
    if not audio_base64_input:
        return {"status": "error", "message": "Aucun 'audio_base64' fourni en entrée."}

    # 2. Préparation des dossiers temporaires
    input_path = "/tmp/input_audio" 
    output_dir = "/tmp/output_rvc"
    
    # Nettoyage pour éviter de saturer la mémoire du conteneur
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    # On supprime aussi l'ancien input s'il existe
    if os.path.exists(input_path):
        os.remove(input_path)

    try:
        # 3. Décodage : Base64 -> Fichier Audio sur le disque
        print("Décodage du vocal entrant...")
        try:
            audio_data = base64.b64decode(audio_base64_input)
            with open(input_path, "wb") as f:
                f.write(audio_data)
        except Exception as e:
            return {"status": "error", "message": f"Base64 invalide: {str(e)}"}

        # 4. Conversion (La magie RVC)
        command = [
            "urvc", "generate", "convert-voice",
            input_path,
            output_dir,
            model_name,
            "--f0-method", "rmvpe",
            "--n-semitones", pitch_change
        ]
        
        print(f"Conversion en cours avec le modèle {model_name}...")
        # On lance la commande (ça prendra quelques secondes selon la longueur du vocal)
        subprocess.run(command, check=True)

        # 5. Récupération du résultat
        output_files = glob.glob(f"{output_dir}/*.wav")
        if not output_files:
            return {"status": "error", "message": "RVC n'a généré aucun fichier."}
        
        final_file = output_files[0]
        
        # 6. Encodage : Fichier Audio -> Base64 pour la réponse
        print("Encodage de la réponse...")
        with open(final_file, "rb") as audio_file:
            # On lit le binaire et on le transforme en string utf-8
            audio_encoded = base64.b64encode(audio_file.read()).decode("utf-8")

        # 7. Réponse JSON directe
        return {
            "status": "success",
            "model": model_name,
            "audio_base64": audio_encoded
        }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Erreur interne RVC: {e}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

runpod.serverless.start({"handler": handler})
