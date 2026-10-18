# Image Python officielle, version fixée et "slim" pour rester légère
FROM python:3.12-slim

WORKDIR /app

# On copie d'abord requirements.txt seul : tant qu'il ne change pas,
# Docker garde cette couche en cache et ne réinstalle pas les bibliothèques
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puis le code de l'API
COPY app/ .

# Utilisateur sans droits : si l'API est piratée, l'attaquant n'est pas root
RUN useradd --no-create-home appuser
USER appuser

EXPOSE 5000

# Un seul worker gunicorn car les parties en cours sont gardées en mémoire
CMD ["gunicorn", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:5000", "main:app"]
