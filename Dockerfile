FROM python:3.13-slim

# 1. Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Crucial: Add the vscode user's local bin to the PATH so 'uvicorn' is found
    PATH="/home/vscode/.local/bin:${PATH}"

# 2. Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    build-essential \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# 3. Create a non-root user (Standard Dev Container practice)
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# 4. Switch to non-root user
USER $USERNAME
WORKDIR /workspaces/StockBot

# 5. Install Python dependencies
# We copy requirements first to leverage Docker layer caching
COPY --chown=vscode:vscode requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 6. Expose the FastAPI port
EXPOSE 8000

# 7. Start the application
# Binding to 0.0.0.0 is mandatory for container networking
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]