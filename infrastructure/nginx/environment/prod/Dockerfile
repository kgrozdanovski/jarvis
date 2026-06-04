FROM nginx:1.29-alpine

# Set environment variable with a default value
ARG APP_ENV=prod

# Copy the frontend's public directory into the container
COPY ./frontend/.output/public /var/www/html/frontend/.output/public

# Ensure the build is running as root
USER root

# Create necessary configuration and certificate directories
RUN mkdir -p /etc/letsencrypt/live/getpoliro.com
RUN mkdir -p /etc/letsencrypt/live/api.getpoliro.com

RUN chown -R nginx:nginx /var/www/html
RUN chmod -R 755 /var/www/html

# Remove original contents of /include
RUN rm -rf /etc/nginx/conf.d/*

# Copy the nginx configuration files based on the environment
COPY ./infrastructure/nginx/environment/${APP_ENV}/nginx.conf /etc/nginx/nginx.conf
# The following lines are for the inactive configuration, dynamically switched by the entrypoint script
COPY ./infrastructure/nginx/environment/${APP_ENV}/include/ /etc/nginx/conf.d/

# Copy the error responses configuration
COPY ./infrastructure/nginx/error_responses.conf /etc/nginx/error_responses.conf

# Expose the HTTP port
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
