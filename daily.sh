#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
SCRIPT="$SCRIPT_DIR/main.py"
CONFIG_DIR="$SCRIPT_DIR/config.yaml"
JOB_FILE="/etc/cron.daily/only-office-backup"

echo "Installing daily job..."
sudo tee "$JOB_FILE" > /dev/null <<EOF
#!/bin/bash
"$VENV_DIR/bin/python" "$SCRIPT" --config "$CONFIG_DIR"
EOF

sudo chmod +x "$JOB_FILE"

echo "Done!"
echo "Script will run once a day."
echo "    > View logs:    tail -f $SCRIPT_DIR/output.log"
echo "    > Test it now:  sudo run-parts /etc/cron.daily"
echo "🗑️  > To uninstall: sudo rm $JOB_FILE"
