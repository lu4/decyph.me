#!/usr/bin/env bash
# Full online setup for decyph.me
#
# Usage:
#   ./python-tools/setup.sh              # full setup
#   ./python-tools/setup.sh --skip-node  # skip Node.js/nvm (if you manage it yourself)
#   ./python-tools/setup.sh --skip-system-deps  # skip Python/Node installation entirely
set -euo pipefail

TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$TOOLS_DIR/.." && pwd)"
NODE_VERSION="22"
SKIP_NODE=false
SKIP_SYSTEM_DEPS=false

# Local installation paths (self-sufficient, independent of repo location)
INSTALL_DIR="$HOME/.local/lib/decyph.me"
INSTALL_SCRIPT="$INSTALL_DIR/decyph.py"
INSTALL_VENV="$INSTALL_DIR/.venv"
INSTALL_VENV_PYTHON="$INSTALL_VENV/bin/python"
BIN_DIR="$HOME/.local/bin"
WRAPPER="$BIN_DIR/decyph.me"

for arg in "$@"; do
    case $arg in
        --skip-node)        SKIP_NODE=true ;;
        --skip-system-deps) SKIP_SYSTEM_DEPS=true ;;
    esac
done

# ── Python 3 + pip ────────────────────────────────────────────────────────────
if [[ "$SKIP_SYSTEM_DEPS" == false ]]; then
    if ! command -v python3 &>/dev/null; then
        echo "==> Installing Python 3..."
        if command -v dnf &>/dev/null; then
            sudo dnf install -y python3 python3-pip
        elif command -v apt-get &>/dev/null; then
            sudo apt-get install -y python3 python3-pip
        elif command -v brew &>/dev/null; then
            brew install python3
        else
            echo "ERROR: Cannot detect package manager. Install Python 3 manually." >&2
            exit 1
        fi
    else
        echo "==> Python $(python3 --version) already installed"
    fi

    if ! python3 -m pip --version &>/dev/null; then
        echo "==> Installing pip..."
        python3 -m ensurepip --upgrade || sudo dnf install -y python3-pip
    fi
fi

# ── Node.js via nvm + npm install ─────────────────────────────────────────────
if [[ "$SKIP_SYSTEM_DEPS" == false && "$SKIP_NODE" == false ]]; then
    export NVM_DIR="$HOME/.nvm"

    if [[ ! -f "$NVM_DIR/nvm.sh" ]]; then
        echo "==> Installing nvm..."
        curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
    else
        echo "==> nvm already installed"
    fi
    # shellcheck disable=SC1090
    source "$NVM_DIR/nvm.sh"

    if ! nvm ls "$NODE_VERSION" &>/dev/null; then
        echo "==> Installing Node.js $NODE_VERSION via nvm..."
        nvm install "$NODE_VERSION"
    else
        echo "==> Node.js $NODE_VERSION already installed via nvm"
    fi
    nvm use "$NODE_VERSION"
fi

echo "==> Installing Node.js dependencies..."
cd "$REPO_DIR"
npm install

# ── Python check ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Re-run without --skip-system-deps." >&2
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
    python3 -m venv "$INSTALL_VENV"
    "$INSTALL_VENV/bin/pip" install --upgrade pip --quiet
    "$INSTALL_VENV/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

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

echo ""
echo "✓ Setup complete!"
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

echo "  To start the web server: npm start"
echo "  To uninstall:            ./python-tools/uninstall.sh"
