# Le Juste Prix

Projet Docker de Yassine Osman, Estaban et Romain Astier.

C'est une version web du jeu Le Juste Prix : il faut trouver un nombre entre 1 et 100, le jeu répond "c'est plus" ou "c'est moins", et les meilleurs scores sont gardés dans une base de données.

## Ce qu'il y a dans la stack

On a 3 services dans le docker-compose :

- front : un Nginx qui sert la page du jeu. Il renvoie aussi tout ce qui commence par /api vers le back.
- back : une petite API en Python (Flask). C'est elle qui tire le nombre secret et vérifie les propositions.
- db : MySQL 8.4, l'image officielle. Elle stocke les pseudos et les scores.

Le navigateur parle seulement au front, le front parle au back, et seul le back parle à la base.

Il y a un Dockerfile pour le back et un pour le front. Pour la base on n'en a pas fait, l'image officielle suffit : on lui donne juste notre script `db/init.sql` qui crée la table au premier démarrage.

## Lancer le projet

Il faut une machine avec Docker et Docker Compose, et le port 80 libre.

```bash
git clone https://github.com/d1styx/juste-prix.git
cd juste-prix
cp .env.example .env
nano .env
docker compose up -d --build
```

Dans le `.env`, il faut changer les deux mots de passe. MySQL met une trentaine de secondes à démarrer la première fois, ensuite le jeu est sur `http://<ip du serveur>`.

Pour vérifier :

```bash
docker compose ps
curl http://localhost/api/scores
```

`docker compose ps` doit montrer les 3 conteneurs "Up", et le curl doit renvoyer `[]` (ou la liste des scores s'il y en a).

Pour arrêter : `docker compose down`. Les scores restent dans le volume, sauf si on ajoute `-v`.

## Sécurité

On a essayé de faire attention à plusieurs choses :

- Les mots de passe ne sont pas dans le docker-compose mais dans un fichier `.env` qui est dans le `.gitignore`. Sur git il n'y a que `.env.example` avec des fausses valeurs.
- Le back n'a pas le mot de passe root de MySQL, seulement celui de son utilisateur.
- Les conteneurs ne tournent pas en root. Dans le Dockerfile du back on crée un utilisateur `appuser`, et pour le front on utilise l'image `nginx-unprivileged`.
- Seul le front ouvre un port sur la machine. La base et l'API ne sont pas accessibles de l'extérieur.
- On a mis deux réseaux Docker, comme ça le front ne peut pas joindre la base directement.
- Les versions des images et des librairies Python sont fixées.
- Le nombre secret reste côté serveur, donc on ne peut pas tricher en regardant le code de la page.

## Les problèmes qu'on a rencontrés

Sur le serveur de l'école (EVA), le premier `docker build` du back a échoué : `pip install` n'arrivait pas à télécharger les librairies ("Network is unreachable"). Le serveur doit passer par le proxy de l'université. On l'a réglé dans `~/.docker/config.json` sur le serveur, pas dans le projet, pour que le projet marche aussi ailleurs :

```json
{
  "proxies": {
    "default": {
      "httpProxy": "http://cache.univ-pau.fr:3128",
      "httpsProxy": "http://cache.univ-pau.fr:3128",
      "noProxy": "localhost,127.0.0.1,db,back,front"
    }
  }
}
```

À cause de ce même proxy, un `curl http://localhost/...` sur le serveur nous renvoyait une erreur 301. Il faut ajouter `--noproxy '*'` pour tester en local.

Ensuite l'API renvoyait une erreur 500. Dans `docker compose logs back` on a vu que PyMySQL avait besoin de la librairie `cryptography` pour se connecter à MySQL 8.4. On l'a ajoutée dans `requirements.txt` et ça a marché.

## Utilisation de l'IA

On s'est aidés d'une IA (Claude) par moments, surtout pour le débogage, les erreurs ci-dessus.
