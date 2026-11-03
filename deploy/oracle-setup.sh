#!/usr/bin/env bash
# Instala y deja corriendo BatBot 24/7 en una VM Ubuntu (Oracle Cloud Always Free).
# Uso, conectado por SSH a la VM:
#   curl -fsSL https://raw.githubusercontent.com/DavidSaboredo/batbot/${BRANCH:-main}/deploy/oracle-setup.sh | BRANCH=main bash
set -euo pipefail

APP_DIR="$HOME/batbot"
REPO="https://github.com/DavidSaboredo/batbot.git"
BRANCH="${BRANCH:-main}"

sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip git

if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull origin "$BRANCH"
else
  git clone -b "$BRANCH" "$REPO" "$APP_DIR"
fi

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

# El token va en un archivo aparte, nunca en el código ni en git
if [ ! -f "$APP_DIR/.env" ]; then
  read -r -s -p "Pegá el DISCORD_TOKEN y apretá Enter: " TOKEN < /dev/tty
  echo
  printf 'DISCORD_TOKEN=%s\nDB_PATH=%s/batbot.db\n' "$TOKEN" "$APP_DIR" > "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
fi

sudo tee /etc/systemd/system/batbot.service > /dev/null <<EOF
[Unit]
Description=BatCompany Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now batbot
sleep 5
sudo systemctl status batbot --no-pager | head -15
echo "Listo. Logs en vivo: journalctl -u batbot -f"
