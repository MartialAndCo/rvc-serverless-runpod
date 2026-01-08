import runpod
import subprocess
import os
import urllib.request
import zipfile
import shutil

# Fonction utilitaire pour télécharger des fichiers (Modèles)
def download_model(url, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = os.path.join(output_dir, "model.zip")
    print(f"Downloading model from {url}...")
    urllib.request.urlretrieve(url, filename)
    
    print("Unzipping...")
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    
    # Nettoyage
    os.remove(filename)
    return f"Modèle installé dans {output_dir}"

def handler(job):
    job_input = job.get("input", {})
    
    # 1. Option "Télécharger un modèle"
    # Entrée: {"method": "download_model", "url": "...", "name": "mon_modele"}
    if job_input.get("method") == "download_model":
        try:
            url = job_input["url"]
            name = job_input.get("name", "custom_model")
            # Ultimate RVC cherche souvent les modèles dans un dossier spécifique, on essaie de le deviner ou on le met à la racine
            # On va le mettre dans /models par défaut
            path = f"/models/{name}"
            result = download_model(url, path)
            return {"status": "success", "message": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # 2. Option "Exécuter une commande" (Le mode Terminal à distance)
    # Entrée: {"command": "urvc --help"}
    # Entrée: {"command": "ls -R"}
    command = job_input.get("command")
    
    if command:
        print(f"Executing: {command}")
        try:
            # On lance la commande et on capture la sortie texte
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "stdout": e.stdout,
                "stderr": e.stderr
            }

    return {"status": "error", "message": "Aucune commande fournie. Essayez {'command': 'urvc --help'}"}

runpod.serverless.start({"handler": handler})
