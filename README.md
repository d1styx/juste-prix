# Le Juste Prix

Projet Docker de Yassine Osman, Estaban et Romain Astier.

C'est une version web du jeu Le Juste Prix : il faut trouver un nombre entre 1 et 100. À chaque proposition le jeu répond "c'est plus" ou "c'est moins", et quand on trouve, le score (le nombre d'essais) est enregistré. Les 10 meilleurs scores s'affichent en bas de la page.

Le but du projet était de faire une stack docker compose avec au moins un front, un back et une base de données, facile à déployer sur une machine Debian avec Docker.


## 1. Ce qu'il y a dans la stack

On a 3 services :

- **front** : un Nginx qui sert la page du jeu (HTML + un peu de JavaScript). Il renvoie aussi tout ce qui commence par `/api` vers le back.
- **back** : une petite API en Python avec Flask. C'est elle qui tire le nombre secret, vérifie les propositions et enregistre les scores.
- **db** : MySQL 8.4, avec l'image officielle. Elle stocke les pseudos et les scores.

Le chemin d'une requête :

```
navigateur  -->  front (Nginx, port 80)  -->  back (Python, port 5000)  -->  db (MySQL, port 3306)
```

Le navigateur parle seulement au front. Le back et la base ne sont pas accessibles depuis l'extérieur.

Les fichiers du projet :

```
juste-prix/
├── docker-compose.yml     les 3 services et comment ils sont reliés
├── .env.example           modèle du fichier de mots de passe
├── .gitignore
├── back/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt   les librairies Python (versions fixées)
│   └── app/main.py        le code de l'API
├── front/
│   ├── Dockerfile
│   ├── nginx.conf         config de Nginx
│   └── html/index.html    la page du jeu
└── db/
    └── init.sql           crée la table des scores
```


## 2. Lancer la stack

### Ce qu'il faut

- Une machine Debian (ou autre Linux) avec Docker et le plugin Docker Compose. Si Docker n'est pas installé, on a suivi la doc officielle : https://docs.docker.com/engine/install/debian/
- Le port 80 libre sur la machine.

Pour vérifier que Docker est prêt :

```bash
docker --version
docker compose version
```

### Installation

On récupère le projet :

```bash
git clone https://github.com/d1styx/juste-prix.git
cd juste-prix
```

On crée le fichier `.env` à partir du modèle :

```bash
cp .env.example .env
nano .env
```

Dans ce fichier il faut changer les deux mots de passe (`MYSQL_ROOT_PASSWORD` et `MYSQL_PASSWORD`). Le nom de la base et l'utilisateur peuvent rester comme ça.

On construit les images et on lance tout :

```bash
docker compose up -d --build
```

La première fois ça prend un peu de temps (téléchargement des images, installation des librairies Python). MySQL met aussi une trentaine de secondes à s'initialiser.

### Vérifier que ça marche

```bash
docker compose ps
```

Les 3 conteneurs (`db`, `back`, `front`) doivent être "Up". Seul le front a un port publié (`0.0.0.0:80->8080`).

```bash
curl http://localhost/api/scores
```

Ça doit répondre `[]` (liste vide) ou la liste des scores s'il y en a déjà.


## 3. Utiliser le jeu

Ouvrir `http://<ip de la machine>` dans un navigateur (chez nous : http://10.3.16.147 sur le serveur EVA de l'école, avec le VPN).

1. On entre un pseudo et on clique sur Jouer.
2. On tape un nombre entre 1 et 100 et on clique sur Proposer.
3. Le jeu répond "C'est plus !" ou "C'est moins !" avec le nombre d'essais.
4. Quand on trouve, le score est enregistré et apparaît dans "Meilleurs scores".

On peut aussi tester l'API directement avec curl :

```bash
# démarrer une partie, la réponse donne un id
curl -X POST -H "Content-Type: application/json" -d '{"pseudo": "test"}' http://localhost/api/partie

# proposer un nombre (remplacer <id> par celui reçu)
curl -X POST -H "Content-Type: application/json" -d '{"id": "<id>", "nombre": 50}' http://localhost/api/essai

# voir le top 10
curl http://localhost/api/scores
```


## 4. Commandes utiles

```bash
docker compose logs back        # voir les logs de l'API (utile en cas d'erreur 500)
docker compose logs -f          # suivre les logs de tous les services
docker compose restart back     # redémarrer un seul service
docker compose stop             # arrêter sans rien supprimer
docker compose down             # supprimer les conteneurs (les scores restent dans le volume)
docker compose down -v          # tout supprimer, scores compris
```

Pour regarder directement dans la base :

```bash
docker compose exec db mysql -u jp_user -p juste_prix -e "SELECT * FROM scores;"
```

(il demande le mot de passe `MYSQL_PASSWORD` du `.env`)

Après une modification du code, on relance juste :

```bash
docker compose up -d --build
```


## 5. Comment on a construit le projet, étape par étape

On a travaillé directement sur le serveur de l'école (un conteneur LXC Debian sur le cluster EVA, accessible en SSH via le VPN).

**Étape 1 : vérifier Docker et créer les dossiers.** On a d'abord vérifié que Docker et Docker Compose marchaient (`docker run hello-world`), puis créé l'arborescence avec un dossier par service, et un `git init`.

**Étape 2 : la base de données.** On n'a pas fait de Dockerfile pour MySQL, l'image officielle `mysql:8.4` suffit. On lui donne juste `db/init.sql`, que MySQL exécute tout seul au premier démarrage (tout ce qui est dans `/docker-entrypoint-initdb.d/`). Ce script crée la table `scores` (id, pseudo, nombre d'essais, date). La base et l'utilisateur sont créés par l'image à partir des variables `MYSQL_DATABASE`, `MYSQL_USER` et `MYSQL_PASSWORD`. On a mis ces variables dans un fichier `.env` plutôt que directement dans le compose comme on avait fait au lab WordPress, pour ne pas mettre les mots de passe sur git.

**Étape 3 : le back.** Une API Flask avec 3 routes :
- `POST /api/partie` : démarre une partie et tire un nombre au hasard. La partie est gardée en mémoire côté serveur.
- `POST /api/essai` : compare le nombre proposé au nombre secret, répond plus / moins / gagné, et enregistre le score en base quand c'est gagné.
- `GET /api/scores` : renvoie les 10 meilleurs scores.

Pour la base on utilise PyMySQL, avec des requêtes paramétrées (`%s`) pour éviter les injections SQL. L'API est lancée avec gunicorn, pas avec le serveur de test de Flask.

**Étape 4 : le Dockerfile du back.** Il part de `python:3.12-slim` (image légère). On copie d'abord `requirements.txt` et on fait le `pip install`, et seulement après on copie le code : comme ça, si on change juste le code, Docker réutilise la couche en cache et ne réinstalle pas les librairies. À la fin on crée un utilisateur `appuser` et on passe dessus avec `USER`, pour que l'API ne tourne pas en root. On l'a testé avec `docker build -t juste-prix-back:v1 back/` comme dans le lab 5.

**Étape 5 : le front.** Une page HTML avec un peu de JavaScript qui appelle l'API avec `fetch`. Nginx sert la page et fait passer `/api/` au back (`proxy_pass http://back:5000`). Pour l'image on a pris `nginxinc/nginx-unprivileged` au lieu de `nginx`, parce qu'elle tourne sans root. Elle écoute sur le port 8080 au lieu de 80, donc dans le compose on fait `80:8080`.

**Étape 6 : le docker-compose.** Il relie les 3 services : `environment` avec les variables du `.env` (`${MYSQL_PASSWORD}`…), un volume `db_data` pour garder les scores, `depends_on` pour l'ordre de démarrage et `restart: unless-stopped`. On a ajouté deux réseaux : `reseau_front` (front + back) et `reseau_back` (back + db), comme ça le front ne peut pas joindre la base.

**Étape 7 : tests et corrections.** On a lancé la stack, testé avec curl puis dans le navigateur, et corrigé les problèmes décrits plus bas. Ensuite README, commit et push sur GitHub.


## 6. Sécurité

Ce qu'on a fait pour la sécurité :

- Les mots de passe sont dans `.env`, qui est dans le `.gitignore`. Sur git il n'y a que `.env.example` avec des fausses valeurs.
- Le back n'a pas le mot de passe root de MySQL, seulement celui de son utilisateur `jp_user`.
- Aucun conteneur qu'on construit ne tourne en root : `appuser` pour le back, `nginx-unprivileged` pour le front.
- Seul le front publie un port. La base et l'API ne sont pas joignables de l'extérieur.
- Deux réseaux séparés : le front ne voit pas la base.
- Les versions des images (`mysql:8.4`, `python:3.12-slim`, `nginx-unprivileged:1.27-alpine`) et des librairies Python sont fixées, pas de `latest`.
- Images légères (`slim` et `alpine`) pour avoir moins de choses installées.
- Le nombre secret reste côté serveur, on ne peut pas tricher en lisant le code de la page.
- Requêtes SQL paramétrées, et les pseudos sont affichés avec `textContent` dans la page pour qu'un pseudo piégé ne puisse pas injecter de code.
- `server_tokens off` dans Nginx pour ne pas afficher sa version.


## 7. Les problèmes qu'on a rencontrés

**pip n'arrivait pas à télécharger les librairies.** Le premier `docker build` du back a échoué avec "Network is unreachable" pendant le `pip install`. Sur le réseau de l'université il faut passer par un proxy. On l'a déclaré dans `~/.docker/config.json` sur le serveur (pas dans le projet, pour que le projet marche aussi ailleurs) :

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

**curl renvoyait une erreur 301.** Sur le serveur, `curl http://localhost/api/scores` répondait "301 Moved Permanently". En fait le serveur a une variable `http_proxy`, donc curl passait par le proxy de l'université au lieu d'aller sur notre Nginx. Avec `curl --noproxy '*' ...` ça marche.

**Erreur 500 sur l'API.** Une fois le proxy réglé, l'API renvoyait une erreur 500. Dans `docker compose logs back` on a trouvé : `'cryptography' package is required for sha256_password or caching_sha2_password auth methods`. MySQL 8.4 utilise par défaut une méthode d'authentification qui demande la librairie `cryptography` côté PyMySQL. On l'a ajoutée dans `requirements.txt`, reconstruit le back, et c'était bon.


## 8. Utilisation de l'IA

On s'est aidés d'une IA (Claude) par moments, surtout pour le débogage (les problèmes ci-dessus).
