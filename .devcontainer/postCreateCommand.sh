#!/bin/bash
DIFY_PLUGIN_LATEST_URL=$(
    curl -s https://api.github.com/repos/langgenius/dify-plugin-daemon/releases/latest \
    | jq -r '.assets[] | select(.name | contains("dify-plugin-linux-amd64")) | .browser_download_url'
)
sudo curl -L -o /usr/local/bin/dify ${DIFY_PLUGIN_LATEST_URL}
sudo chmod +x /usr/local/bin/dify

echo 'export PYTHONDONTWRITEBYTECODE=1' >> ~/.bashrc
