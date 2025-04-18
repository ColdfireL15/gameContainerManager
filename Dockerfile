# Use official Python image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY ./data .

# Set environment(s) variable(s)
ENV DOCKERCONTAINERMANAGER_DEBUG=FALSE
ENV DISCORD_TOKEN=

# Install python dependencies
RUN pip install -r requirements.txt

# Make the script executable
RUN chmod +x entrypoint.sh

# Expose necessary ports
EXPOSE 5000

# Set the script as entry point
ENTRYPOINT ["./entrypoint.sh"]
