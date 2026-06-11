FROM mcr.microsoft.com/devcontainers/universal:2

# Step 1: Fix the legacy Yarn source GPG error
RUN sudo rm -f /etc/apt/sources.list.d/yarn.list

# Step 2: Install Claude Code globally 
RUN npm install -g @anthropic-ai/claude-code

# Step 3: Create the working directory inside the image
WORKDIR /workspaces/groceries_plugin

# Step 4: Copy the zipped project files into the container image build context
COPY claude_project/uigen.zip ./claude_project/

# Step 5: Unzip and run the setup inside the image during the build
RUN cd claude_project && \
    unzip -o uigen.zip && \
    npm install && \
    npm run setup