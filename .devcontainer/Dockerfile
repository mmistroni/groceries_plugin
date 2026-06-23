# Use a high-quality, pre-configured image that already has Node.js and standard tools
FROM mcr.microsoft.com/devcontainers/javascript-node:1-20-bullseye

# Install unzip so we can extract the course files later
RUN apt-get update && apt-get install -y unzip && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code