# applications/frontend/Dockerfile

FROM nginx:alpine

# Copy our custom NGINX config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static frontend files
COPY src/ /usr/share/nginx/html/

# Expose HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
