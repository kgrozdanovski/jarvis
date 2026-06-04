FROM nginx:1.29-alpine

# Set environment variable with a default value
ARG APP_ENV=dev

# Copy the frontend's public directory into the container
COPY ./frontend/.output/public /var/www/html/frontend/.output/public

# Ensure the build is running as root
USER root

# Create necessary configuration and certificate directories
RUN mkdir -p /etc/letsencrypt/live/jarvis.local
RUN mkdir -p /etc/letsencrypt/live/api.jarvis.local

RUN chown -R nginx:nginx /var/www/html
RUN chmod -R 755 /var/www/html

# Copy the nginx configuration files based on the environment
COPY ./infrastructure/nginx/environment/${APP_ENV}/nginx.conf /etc/nginx/nginx.conf
# The following lines are for the inactive configuration, dynamically switched by the entrypoint script
COPY ./infrastructure/nginx/environment/${APP_ENV}/include/ /etc/nginx/conf.d/

# Copy the error responses configuration
COPY ./infrastructure/nginx/error_responses.conf /etc/nginx/error_responses.conf

# Additional setup for self-signed certificates
RUN apk add --no-cache openssl

RUN mkdir -p /etc/nginx/selfsigned

RUN openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout /etc/nginx/selfsigned/privkey.pem \
    -out /etc/nginx/selfsigned/fullchain.pem \
    -subj "/CN=localhost" && \
    chmod 644 /etc/nginx/selfsigned/privkey.pem && \
    chmod 644 /etc/nginx/selfsigned/fullchain.pem

# Expose the HTTP port
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
