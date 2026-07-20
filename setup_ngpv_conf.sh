#!/usr/bin/env bash
# Sorgt dafür, dass /etc/gpib.conf einen korrekten ngpv-Block (PAD 12) enthält,
# und lädt die Conf in den linux-gpib-Treiber.
#
# Idempotent: legt den Block an, wenn er fehlt, und korrigiert den pad-Wert,
# wenn er abweicht. Ist beides in Ordnung, wird nichts geschrieben.
#
# Hintergrund: Am 2026-05-25 hat die Arbeit an einem zweiten GPIB-Gerät
# (Xantrex XT 20-3) den pad-Wert des ngpv-Blocks von 12 auf 2 verstellt.
# Das fällt nur als "Gerät antwortet nicht" auf. Dieses Skript stellt den
# dokumentierten Zustand wieder her.
#
# Aufruf:
#   bash setup_ngpv_conf.sh
# (sudo wird intern aufgerufen, du wirst nach dem Passwort gefragt)

set -euo pipefail

CONF=/etc/gpib.conf
NAME=ngpv
PAD=12          # Werks-Default, per DIP an der NGPV-Rückwand gesetzt.
                # Wird nur beim Power-On des Geräts gelatcht.

backup() {
    local dst="$CONF.bak.$(date +%Y%m%d-%H%M%S)"
    echo "[backup] $CONF -> $dst"
    sudo cp "$CONF" "$dst"
}

if [ ! -e "$CONF" ]; then
    echo "[fehler] $CONF existiert nicht — ist linux-gpib installiert?" >&2
    exit 1
fi

if ! grep -q "name[[:space:]]*=[[:space:]]*\"$NAME\"" "$CONF"; then
    backup
    echo "[append] ${NAME}-Block (PAD $PAD) -> $CONF"
    sudo tee -a "$CONF" >/dev/null <<EOF

/* R&S NGPV 40/5 — Listener-only Gerät.
 * Default-Adresse vom Werk = $PAD (Rückwand-DIP); falls am Gerät anders
 * eingestellt: pad-Wert hier anpassen.
 */
device {
	minor       = 0
	name        = "$NAME"
	pad         = $PAD
	sad         = 0

	eos         = 0x0a
	set-reos    = no
	set-bin     = no
}
EOF
else
    # Block da — pad innerhalb genau dieses Blocks auslesen (bis zur schließenden
    # Klammer), damit Einträge anderer Geräte nicht mitgelesen werden.
    IST=$(awk -v n="$NAME" '
        $0 ~ "name[[:space:]]*=[[:space:]]*\""n"\"" {in_block=1}
        in_block && /pad[[:space:]]*=/ {gsub(/[^0-9]/,"",$0); print; exit}
    ' "$CONF")

    if [ "$IST" = "$PAD" ]; then
        echo "[skip] ${NAME}-Block ist bereits korrekt (pad = $PAD)."
    else
        echo "[fix] ${NAME}-Block hat pad = ${IST:-?}, erwartet $PAD."
        backup
        sudo sed -i "/name[[:space:]]*=[[:space:]]*\"$NAME\"/,/}/ s/^\(\s*pad\s*=\s*\)[0-9]\+/\1$PAD/" "$CONF"
        echo "[ok] pad auf $PAD korrigiert."
    fi
fi

echo
echo "[verify] ${NAME}-Block in $CONF:"
awk -v n="$NAME" '
    $0 ~ "name[[:space:]]*=[[:space:]]*\""n"\"" {in_block=1}
    in_block {print}
    in_block && /}/ {exit}
' "$CONF"

echo
echo "[reload] sudo gpib_config"
sudo gpib_config

echo
echo "[ok] $NAME ist im Treiber registriert. Test: ngpv 5v"
