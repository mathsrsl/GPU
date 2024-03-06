import subprocess
import os

# Créer le répertoire 'export' s'il n'existe pas
os.makedirs('export', exist_ok=True)

# Installez les dépendances depuis le fichier requirements.txt
subprocess.run(["pip", "install", "-r", "requirements.txt"])

print("\n---------- Le programme est prêt à être utilisé. ----------\n")