FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/vscode/.local/bin:${PATH}" \
    PYTHONPATH="/workspaces/StockBot/src/Python"

RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    build-essential \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# User setup
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
WORKDIR /workspaces/StockBot

# Copy all files
COPY --chown=vscode:vscode . .

RUN pip install --no-cache-dir --user -r requirements.txt

EXPOSE 8000

# Points to Scraper inside src/Python
CMD ["python", "-m", "uvicorn", "src.Python.Scraper:app", "--host", "0.0.0.0", "--port", "8000"]