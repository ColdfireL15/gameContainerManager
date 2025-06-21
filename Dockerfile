# Use official Python image as base
FROM python:3.12-alpine3.21

# Set working directory
WORKDIR /app

# Copy project files
COPY ./data .

# Set environment(s) variable(s)
ENV DOCKERCONTAINERMANAGER_AUTHENTICATION="False"
ENV DOCKERCONTAINERMANAGER_DEBUG="False"
ENV DOCKERCONTAINERMANAGER_BACKEND_URL="http://backend:5000"
ENV DOCKERCONTAINERMANAGER_FAVICON_URL='./static/icon/gameContainerManager.ico'
ENV DOCKERCONTAINERMANAGER_SERVICE_TYPE=frontend

# Install python dependencies
RUN pip install -r requirements.txt

# Make the script executable
RUN chmod +x entrypoint.sh

# Expose necessary ports
EXPOSE 5000


# HEALTHCHECK
RUN apk add --no-cache curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

# Set the script as entry point
ENTRYPOINT ["./entrypoint.sh"]
