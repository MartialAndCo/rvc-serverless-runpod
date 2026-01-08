import runpod
import os

# On tente d'importer RVC pour vérifier que l'installation a réussi au démarrage
try:
    # Ceci est juste pour vérifier que la librairie est bien là
    import ultimate_rvc
    print("Ultimate RVC library found and imported.")
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import ultimate_rvc: {e}")

def handler(job):
    job_input = job['input']
    
    # Simple echo pour le moment pour valider le serverless
    return {
        "status": "success",
        "message": "Le container fonctionne, RVC est installé.",
        "python_version": os.popen("python --version").read().strip()
    }

runpod.serverless.start({"handler": handler})
