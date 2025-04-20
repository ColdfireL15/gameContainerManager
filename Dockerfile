# Use official Python image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY ./data .

# Set environment(s) variable(s)
ENV DOCKERCONTAINERMANAGER_DEBUG=False
ENV DOCKERCONTAINERMANAGER_AUTHENTICATION=True
ENV DOCKERCONTAINERMANAGER_FAVICON_URL=https://mondomaine.com/favicon.ico
# Install python dependencies
RUN pip install -r requirements.txt

# Make the script executable
RUN chmod +x entrypoint.sh

# Expose necessary ports
EXPOSE 5000

# Set the script as entry point
ENTRYPOINT ["./entrypoint.sh"]
