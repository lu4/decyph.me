#!/usr/bin/env bash
# Offline setup for Fedora live USB.
#
# STEP 1 — run on an online machine to pre-download all dependencies:
#   ./python-tools/setup-offline.sh --bundle
#   Then copy the whole repo (including python-tools/wheels/ and node_modules/) to the USB.
#
# STEP 2 — run on the live USB (no internet required):
#   ./python-tools/setup-offline.sh
set -euo pipefail

TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$TOOLS_DIR/.." && pwd)"
WHEELS_DIR="$TOOLS_DIR/wheels"

# Local installation paths (self-sufficient, independent of repo location)
INSTALL_DIR="$HOME/.local/lib/decyph.me"
INSTALL_SCRIPT="$INSTALL_DIR/decyph.py"
INSTALL_VENV="$INSTALL_DIR/.venv"
INSTALL_VENV_PYTHON="$INSTALL_VENV/bin/python"
BIN_DIR="$HOME/.local/bin"
WRAPPER="$BIN_DIR/decyph.me"

# ── Bundle mode (online machine) ──────────────────────────────────────────────
if [[ "${1:-}" == "--bundle" ]]; then
    mkdir -p "$WHEELS_DIR"

    echo "==> Downloading get-pip.py bootstrap ..."
    curl -fsSL https://bootstrap.pypa.io/get-pip.py -o "$WHEELS_DIR/get-pip.py"

    echo "==> Downloading pip wheel ..."
    pip download --dest "$WHEELS_DIR" pip setuptools wheel

    echo "==> Downloading Python dependency wheels ..."
    pip download \
        --dest "$WHEELS_DIR" \
        -r "$TOOLS_DIR/requirements.txt"

    echo "==> Running npm install (node_modules/ will be copied to USB)..."
    cd "$REPO_DIR"
    npm install

    echo ""
    echo "✓ Bundle ready. Copy this entire repo to the USB, then run: ./python-tools/setup-offline.sh"
    exit 0
fi

# ── Install mode (live USB, no internet) ─────────────────────────────────────
echo "==> Offline setup for decyph.me"

if curl -fsSL --max-time 3 https://pypi.org &>/dev/null; then
    echo ""
    echo "Internet is available — this script is intended for offline use on a Fedora live USB."
    echo "Since you're online, you likely want one of the following instead:"
    echo ""
    echo "  1) Bundle for offline USB"
    echo "       Downloads all Python wheels and runs npm install so the repo can be copied"
    echo "       to a Fedora live USB and used without internet. Choose this if you're"
    echo "       preparing the repo on your main machine before taking it offline."
    echo ""
    echo "  2) Full online setup"
    echo "       Installs system dependencies (Python, Node.js via nvm), creates a venv,"
    echo "       and installs decyph.me as a local command. Choose this if you just want"
    echo "       to use decyph.me on this machine."
    echo ""
    echo "  3) Continue with offline install anyway"
    echo "       Proceeds with this script as-is. Only makes sense if you already have"
    echo "       wheels bundled in python-tools/wheels/ and want to test the offline flow."
    echo ""
    read -rp "Choice [1/2/3]: " choice
    case $choice in
        1) exec "$0" --bundle ;;
        2) exec "$(dirname "$0")/setup.sh" ;;
        3) ;;
        *) echo "Aborted." ; exit 0 ;;
    esac
fi

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found on this system." >&2
    exit 1
fi

if [[ ! -d "$WHEELS_DIR" ]] || [[ -z "$(ls -A "$WHEELS_DIR" 2>/dev/null)" ]]; then
    echo "ERROR: $WHEELS_DIR is empty."
    echo "  Run './python-tools/setup-offline.sh --bundle' on an online machine first." >&2
    exit 1
fi

# ── Install decyph.me (self-sufficient local install) ─────────────────────────
if [[ -f "$WRAPPER" ]]; then
    echo "==> decyph.me already installed at $WRAPPER — skipping"
else
    echo "==> Installing decyph.me to $INSTALL_DIR ..."
    mkdir -p "$INSTALL_DIR"

    cp "$TOOLS_DIR/decyph.py" "$INSTALL_SCRIPT"
    cp "$TOOLS_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt"

    echo "==> Creating isolated virtualenv at $INSTALL_VENV ..."
    python3 -m venv --without-pip "$INSTALL_VENV"

    echo "==> Bootstrapping pip from local wheels ..."
    "$INSTALL_VENV/bin/python" "$WHEELS_DIR/get-pip.py" \
        --no-index \
        --find-links "$WHEELS_DIR" \
        --quiet

    "$INSTALL_VENV/bin/pip" install \
        --no-index \
        --find-links "$WHEELS_DIR" \
        -r "$INSTALL_DIR/requirements.txt"

    mkdir -p "$BIN_DIR"
    cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
# script: $INSTALL_SCRIPT
# python: $INSTALL_VENV_PYTHON
# venv:   $INSTALL_VENV
# deps:   $INSTALL_DIR/requirements.txt
exec "$INSTALL_VENV_PYTHON" "$INSTALL_SCRIPT" "\$@"
EOF
    chmod +x "$WRAPPER"
    echo "==> Installed decyph.me → $WRAPPER"
fi

if [[ ! -d "$REPO_DIR/node_modules" ]]; then
    echo ""
    echo "WARNING: node_modules/ not found — web server unavailable."
    echo "  Copy node_modules/ from the online machine to use it offline."
fi

echo ""
echo "✓ Offline setup complete!"
echo ""
echo "  command : decyph.me"
echo "  script  : $INSTALL_SCRIPT"
echo "  python  : $INSTALL_VENV_PYTHON"
echo "  venv    : $INSTALL_VENV"
echo "  deps    : $INSTALL_DIR/requirements.txt"
echo ""

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "  NOTE: Add ~/.local/bin to your PATH to use decyph.me anywhere:"
    echo '    export PATH="$HOME/.local/bin:$PATH"'
    echo ""
fi

echo "  To start the web server (if node_modules present): node server.js"
echo "  To uninstall: ./python-tools/uninstall.sh"
