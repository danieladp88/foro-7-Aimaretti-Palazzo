FROM nginxinc/nginx-unprivileged:1.27-alpine

USER root

RUN apk add --no-cache curl

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html

USER 101

EXPOSE 8080