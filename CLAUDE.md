# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-implementation QR encryption project that provides secure text encryption with QR code generation. The project consists of both Python CLI tools and a web application for encrypting/decrypting text using AES-256-GCM with Scrypt key derivation.

## Commands

### Node.js Web Application
```bash
# Install dependencies
npm install

# Start the web server (development and production)
npm start
# or
npm run dev

# Test locally
# Visit http://localhost:3000
```

### Python CLI Tools
```bash
# Navigate to Python tools directory
cd python-tools

# Install Python dependencies
pip install -r requirements.txt

# Note: QR decoding requires zbar system library
# - macOS: brew install zbar
# - Ubuntu/Debian: sudo apt-get install libzbar0
# - Fedora: sudo dnf install zbar

# === UNIFIED TOOL (Recommended) ===
# decyph.py - All-in-one encryption/decryption with QR support
# SECURITY: Passwords/data are NEVER command-line args (shell history leak prevention)
#           Always prompted securely or piped from stdin
#           Comprehensive security warnings before sensitive operations

# CONTEXT-AWARE ARGUMENTS:
# Same argument name adapts based on mode (encrypt vs decrypt):
# --qr-code, --url, --base64: OUTPUT in -e mode, INPUT in -d mode
# --clipboard: WRITE in -e mode, READ in -d mode

# Encryption (interactive - prompts for text and password)
python decyph.py -e
python decyph.py -e --qr-code                   # Show QR on screen
python decyph.py -e --qr-code qr.png            # Save as QR PNG
python decyph.py -e --url link.txt              # Save full URL to file
python decyph.py -e --base64 data.txt           # Save base64 to file

# Multiple outputs simultaneously (encrypt only)
python decyph.py -e --qr-code qr.png --url link.txt --base64 data.b64

# Encryption (piped - SECURE methods only)
cat file.txt | python decyph.py -e --qr-code qr.png  # From file (SECURE)
pbpaste | python decyph.py -e                        # From clipboard (SECURE)

# ⚠️ NEVER use echo with sensitive data:
# echo "Secret" | python decyph.py -e  # ❌ INSECURE! Saves in shell history

# Decryption (interactive - prompts for data and password)
python decyph.py -d
python decyph.py -d --url encrypted.txt         # Read from URL file
python decyph.py -d --base64 data.txt           # Read from base64 file
python decyph.py -d --qr-code                   # Prompts for QR path
python decyph.py -d --qr-code qr.png            # Scan QR → decrypt
python decyph.py -d --clipboard                 # Clipboard QR → decrypt

# Decryption (piped - SECURE methods only)
cat encrypted.txt | python decyph.py -d  # From file (SECURE)
pbpaste | python decyph.py -d            # From clipboard (SECURE)

# ⚠️ NEVER use echo with encrypted data:
# echo "ARIIAYJo..." | python decyph.py -d  # ❌ INSECURE! Saves in shell history

# QR code operations (no encryption)
python decyph.py --encode-qr qr.png             # Plain text → QR PNG
python decyph.py --encode-qr                    # Plain text → QR screen
python decyph.py --decode-qr qr.png             # QR image → text
python decyph.py --decode-qr                    # QR image → text (prompts for path)

# Advanced (custom QR styling)
python decyph.py -e --qr-code qr.png -b 30 --fill blue --back yellow

# Quiet mode (suppress security warnings - use with caution!)
python decyph.py -e -q

# === MINIMAL TOOL ===
# decrypt_qr_minimal.py - 7-line minimal decryption
python decrypt_qr_minimal.py

# === LEGACY TOOLS (functionality in decyph.py) ===
# encrypt_qr.py, decode_qr.py, file_to_qr.py, generate_qr.py
# See python-tools/LEGACY_TOOLS.md for details
```

### Heroku Deployment
```bash
# Set Node.js buildpack (important!)
heroku buildpacks:set heroku/nodejs

# Deploy to Heroku (requires git repo initialization)
heroku create your-app-name
git push heroku main

# Scale web dyno
heroku ps:scale web=1

# App uses heroku-24 stack with Node.js 22.x LTS
# Stack and Node version are automatically configured
```

**Current deployment**: https://decyph-me-a891b63bc842.herokuapp.com/

## Architecture

### Dual Implementation Structure
The project maintains two parallel implementations of the same encryption scheme:

1. **Python CLI Tools** (`python-tools/decyph.py` - unified tool, `decrypt_qr_minimal.py`)
   - Command-line interface for encryption/decryption
   - Uses Python's `cryptography` library for crypto operations
   - Direct QR code generation with `qrcode[pil]`
   - QR code decoding from images with `pyzbar`
   - **decyph.py** - All-in-one tool combining encryption, decryption, QR generation/decoding
   - **decrypt_qr_minimal.py** - 7-line minimal decryption tool
   - Legacy tools: `encrypt_qr.py`, `decode_qr.py`, `file_to_qr.py`, `generate_qr.py`

2. **Web Application** (`server.js`, `public/index.html`)
   - Browser-based interface with identical functionality
   - Uses Web Crypto API for AES-GCM operations
   - Client-side JavaScript with scrypt-js and qrcodejs libraries
   - Express server serves static files for Heroku deployment

### Encryption Scheme Compatibility
Both implementations use identical cryptographic parameters to ensure cross-compatibility:
- **Scrypt KDF**: N=2^18 (262,144), r=8, p=1
- **AES-256-GCM** encryption with 16-byte salt, 12-byte nonce
- **Password requirements**: Minimum 14 characters, 3+ character classes
- **Base64 URL-safe encoding** for shareable data
- **Format version**: V1 with 4-byte header for future compatibility

### Web Application Auto-Detection
The web app includes URL fragment detection for encrypted data. When accessing URLs ending with `qr#{base64_data}`, it automatically:
- Switches to decrypt mode
- Pre-fills the encrypted data field
- Shows a detection banner
- Focuses the password input

### External Dependencies
- **Python**: `cryptography==41.0.7`, `qrcode[pil]==7.4.2`, `pillow>=10.0.0`, `pyzbar>=0.1.9`
  - **System dependency for decode_qr.py**: zbar library (libzbar)
- **JavaScript**: scrypt-js v3.0.1, qrcodejs v1.0.0 (both from cdnjs.cloudflare.com)
- **Node.js**: Express v4.18.2, qrcode v1.5.3 for server-side QR generation
- **Runtime**: Node.js 22.x LTS (heroku-24 stack)

### Deployment Structure
```
├── python-tools/ (Python CLI tools - isolated from Heroku)
├── server.js (Express server)
├── public/index.html (web app - copy of encrypt_qr.html)
├── Procfile (Heroku configuration)
└── package.json (Node.js configuration)
```

## Important Implementation Notes

### JavaScript Crypto Library Usage
- **Scrypt access**: Use `scrypt.scrypt()` method (not global `scrypt()`)
- **Library loading**: Both scrypt-js and qrcodejs must be loaded before use
- **QR generation**: qrcodejs creates img elements in containers, not canvas elements
- **Error handling**: Libraries may fail to load; implement proper fallbacks

### Python-JavaScript Compatibility
When modifying crypto parameters or data formats, ensure both implementations remain compatible:
- Header format: `[VER, LOGN, R, P]` bytes
- Unicode normalization: NFC for passwords
- Base64 URL-safe encoding without padding
- AAD (Additional Authenticated Data): header + salt + nonce