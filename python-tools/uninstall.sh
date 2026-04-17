#!/usr/bin/env bash
# Uninstalls decyph.me (and/or legacy decyph/decyph.py) from ~/.local/bin
# and removes ~/.local/lib/decyph.me
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
INSTALL_DIR="$HOME/.local/lib/decyph.me"

WRAPPER_NEW="$BIN_DIR/decyph.me"
WRAPPER_PY="$BIN_DIR/decyph.py"
WRAPPER_OLD="$BIN_DIR/decyph"

found=()
[[ -f "$WRAPPER_NEW" ]] && found+=("$WRAPPER_NEW")
[[ -f "$WRAPPER_PY"  ]] && found+=("$WRAPPER_PY")
[[ -f "$WRAPPER_OLD" ]] && found+=("$WRAPPER_OLD")

if [[ ${#found[@]} -eq 0 ]]; then
    echo "Nothing to uninstall — no decyph.me, decyph.py, or decyph found in $BIN_DIR"
    exit 0
fi

if [[ ${#found[@]} -gt 1 ]]; then
    echo "Multiple installations found:"
    for i in "${!found[@]}"; do
        echo "  $((i+1))) ${found[$i]}"
    done
    echo "  $((${#found[@]}+1))) All"
    read -rp "Which to uninstall? [1-$((${#found[@]}+1))]: " choice
    if [[ "$choice" -eq $((${#found[@]}+1)) ]]; then
        targets=("${found[@]}")
    elif [[ "$choice" -ge 1 && "$choice" -le ${#found[@]} ]]; then
        targets=("${found[$((choice-1))]}")
    else
        echo "Aborted." ; exit 1
    fi
else
    targets=("${found[0]}")
    read -rp "Uninstall ${targets[0]}? [y/N]: " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted." ; exit 0 ; }
fi

for t in "${targets[@]}"; do
    rm "$t"
    echo "✓ Removed $t"
done

# Remove install dir if decyph.me wrapper was among the targets
if [[ " ${targets[*]} " == *" $WRAPPER_NEW "* ]] && [[ -d "$INSTALL_DIR" ]]; then
    read -rp "Also remove $INSTALL_DIR (script + venv)? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        echo "✓ Removed $INSTALL_DIR"
    fi
fi
