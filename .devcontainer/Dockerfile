# Use the default universal Codespaces image which already has Node, Git, and permissions configured
FROM mcr.microsoft.com/devcontainers/universal:2

# Switch to root just to install unzip safely
USER root

# Install unzip utility
RUN apt-get update && apt-get install -y unzip && apt-get clean && rm -rf /var/lib/apt/lists/*

# Switch back to the default Codespaces user
USER codespace