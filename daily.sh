#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="only-office-backup.service"
TIMER_NAME="only-office-backup.timer"

mkdir -p "$UNIT_DIR"

echo "Installing systemd user service + timer..."
cat > "$UNIT_DIR/$SERVICE_NAME" <<EOF
[Unit]
Description=OnlyOffice backup

[Service]
Type=oneshot
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/run.sh
EOF

cat > "$UNIT_DIR/$TIMER_NAME" <<EOF
[Unit]
Description=Run OnlyOffice backup daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now "$TIMER_NAME"

echo "Done!"
echo "Timer installed and will run once a day."
echo "    > View logs:      tail -f $SCRIPT_DIR/output.log"
echo "    > View journal:   journalctl --user -u $SERVICE_NAME"
echo "    > Check schedule: systemctl --user list-timers $TIMER_NAME"
echo "    > Test it now:    systemctl --user start $SERVICE_NAME"
echo "🗑️  > To uninstall:   systemctl --user disable --now $TIMER_NAME && rm $UNIT_DIR/$SERVICE_NAME $UNIT_DIR/$TIMER_NAME"
