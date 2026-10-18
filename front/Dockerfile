# Variante officielle de nginx qui tourne sans root, version fixée
FROM nginxinc/nginx-unprivileged:1.27-alpine

# Notre config remplace celle par défaut
COPY nginx.conf /etc/nginx/conf.d/default.conf

# La page du jeu
COPY html/ /usr/share/nginx/html/

EXPOSE 8080
