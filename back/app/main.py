# API du Juste Prix : tire le nombre secret et vérifie les propositions
import os
import random
import uuid

import pymysql
from flask import Flask, jsonify, request

app = Flask(__name__)

# Parties en cours, gardées en mémoire. Le nombre secret reste sur le serveur,
# le navigateur ne le voit jamais : pas de triche possible.
parties = {}


def connexion_db():
    # "db" est le nom du service MySQL dans docker-compose
    return pymysql.connect(
        host="db",
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
    )


@app.post("/api/partie")
def nouvelle_partie():
    pseudo = request.json.get("pseudo", "anonyme")[:30]
    id_partie = uuid.uuid4().hex
    parties[id_partie] = {"secret": random.randint(1, 100), "essais": 0, "pseudo": pseudo}
    return jsonify(id=id_partie)


@app.post("/api/essai")
def essai():
    id_partie = request.json.get("id")
    partie = parties.get(id_partie)
    if partie is None:
        return jsonify(erreur="partie inconnue"), 404

    nombre = int(request.json.get("nombre", 0))
    partie["essais"] += 1

    if nombre < partie["secret"]:
        return jsonify(resultat="plus", essais=partie["essais"])
    if nombre > partie["secret"]:
        return jsonify(resultat="moins", essais=partie["essais"])

    # Gagné : on enregistre le score puis on supprime la partie
    db = connexion_db()
    with db.cursor() as cur:
        # Requête avec %s : pymysql échappe les valeurs, pas d'injection SQL
        cur.execute("INSERT INTO scores (pseudo, essais) VALUES (%s, %s)",
                    (partie["pseudo"], partie["essais"]))
    db.commit()
    db.close()
    del parties[id_partie]
    return jsonify(resultat="gagne", essais=partie["essais"])


@app.get("/api/scores")
def scores():
    db = connexion_db()
    with db.cursor() as cur:
        cur.execute("SELECT pseudo, essais FROM scores ORDER BY essais LIMIT 10")
        lignes = cur.fetchall()
    db.close()
    return jsonify([{"pseudo": p, "essais": e} for p, e in lignes])
