FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Minimal OS deps for typical Python dev + building some wheels
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (Dev Containers convention)
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash \
    && apt-get update && apt-get install -y sudo \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && rm -rf /var/lib/apt/lists/*

USER $USERNAME

# IMPORTANT:
# Do NOT COPY your project into the image.
# VS Code will mount your local folder into /workspaces/<folder-name>.
WORKDIR /workspaces/workspace
