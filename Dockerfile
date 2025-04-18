# Utiliser une image Python officielle comme base
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers du projet
COPY ./data .

# Installer les dépendances
RUN pip install -r requirements.txt

# Rendre le script exécutable
RUN chmod +x entrypoint.sh

# Exposer les ports nécessaires
EXPOSE 5000

# Définir le script comme point d'entrée
ENTRYPOINT ["./entrypoint.sh"]
