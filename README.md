# Le Juste Prix

Projet Docker réalisé par Yassine Osman, Estaban et Romain Astier.

Une version web du jeu « Le Juste Prix » : le joueur doit trouver un nombre secret entre 1 et 100, le jeu lui répond « c'est plus » ou « c'est moins », et les meilleurs scores sont enregistrés en base.

## Architecture

La stack contient 3 services, lancés par `docker compose` :

```
Navigateur ──> front (Nginx, port 80) ──> back (API Python) ──> db (MySQL)
```

| Service | Image | Rôle |
|---------|-------|------|
| `front` | construite depuis `front/Dockerfile` (base `nginx-unprivileged:1.27-alpine`) | Sert la page du jeu et transmet les appels `/api` au back |
| `back` | construite depuis `back/Dockerfile` (base `python:3.12-slim`) | API Flask : tire le nombre secret, vérifie les propositions, enregistre les scores |
| `db` | `mysql:8.4` (image officielle) | Stocke les pseudos et les scores |

Organisation des fichiers :

```
juste-prix/
├── docker-compose.yml   # définition des 3 services
├── .env.example         # modèle des variables (sans vrais mots de passe)
├── back/
│   ├── Dockerfile
│   ├── requirements.txt # bibliothèques Python, versions fixées
│   └── app/main.py      # code de l'API
├── front/
│   ├── Dockerfile
│   ├── nginx.conf       # config Nginx (page + redirection /api)
│   └── html/index.html  # page du jeu
└── db/
    └── init.sql         # création de la table des scores
```

## Prérequis

- Une machine Debian avec Docker et le plugin Docker Compose
- Le port 80 libre

## Installation

```bash
git clone <url-du-depot> juste-prix
cd juste-prix

# Créer le fichier des secrets à partir du modèle
cp .env.example .env
nano .env    # remplacer les deux mots de passe

# Construire les images et lancer la stack
docker compose up -d --build
```

Au premier lancement, MySQL a besoin d'environ 30 secondes pour s'initialiser.

Le jeu est ensuite accessible sur `http://<ip-du-serveur>`.

## Vérifier que tout marche

```bash
docker compose ps                         # les 3 services doivent être "Up"
curl http://localhost/api/scores          # doit répondre [] ou la liste des scores
docker compose logs back                  # en cas d'erreur côté API
```

## Commandes utiles

```bash
docker compose stop      # arrêter sans rien supprimer
docker compose down      # supprimer les conteneurs (les scores sont gardés dans le volume)
docker compose down -v   # tout supprimer, y compris les scores
```

## Choix techniques et sécurité

- **Un conteneur par service** : la base, l'API et le serveur web sont séparés, on peut les mettre à jour indépendamment.
- **Pas de mot de passe dans le code** : les identifiants MySQL sont dans `.env`, qui est dans le `.gitignore`. Seul `.env.example` est versionné.
- **Le back n'a pas le mot de passe root** de MySQL, seulement celui de son compte applicatif.
- **Conteneurs sans root** : le back tourne avec un utilisateur `appuser` créé dans le Dockerfile, et le front utilise la variante `nginx-unprivileged`.
- **Un seul port exposé** : seul le front publie un port (80). La base et l'API ne sont pas joignables depuis l'extérieur.
- **Deux réseaux Docker** : `reseau_front` (front et back) et `reseau_back` (back et base). Le front ne peut donc pas parler directement à la base.
- **Versions fixées** pour les images et les bibliothèques Python, pour que la construction donne le même résultat partout.
- **Images légères** : variantes `slim` et `alpine`.
- **Pas de triche** : le nombre secret est tiré et gardé côté serveur, le navigateur ne le reçoit jamais.
- **Requêtes SQL paramétrées** pour éviter les injections, et affichage des pseudos avec `textContent` côté page.
- `server_tokens off` dans Nginx pour ne pas afficher sa version.

## Note pour le serveur de l'école (EVA)

Sur le réseau de l'université, les constructions d'images n'ont pas d'accès direct à Internet (`pip install` échoue). Il faut déclarer le proxy de l'université dans `~/.docker/config.json`, sur le serveur uniquement :

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

Ce réglage n'est pas dans le projet, qui reste donc déployable sur n'importe quelle machine sans proxy. Pour tester avec `curl` sur ce serveur, ajouter `--noproxy '*'`.
