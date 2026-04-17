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
# Setup (installs decyph.me command to ~/.local/bin — self-sufficient, no repo needed after)
./python-tools/setup.sh

# === UNIFIED TOOL (Recommended) ===
# After setup, invoke from anywhere as:
decyph.me -e
decyph.me -d

# Or run directly from the repo:
python python-tools/decyph.py -e

# SECURITY: Passwords/data are NEVER command-line args (shell history leak prevention)
#           Always prompted securely or piped from stdin
#           Comprehensive security warnings before sensitive operations

# CONTEXT-AWARE ARGUMENTS:
# Same argument name adapts based on mode (encrypt vs decrypt):
# --qr-code, --url, --base64: OUTPUT in -e mode, INPUT in -d mode
# --clipboard: WRITE in -e mode, READ in -d mode

# Encryption (interactive - prompts for text and password)
decyph.me -e
decyph.me -e --qr-code                   # Show QR on screen
decyph.me -e --qr-code qr.png            # Save as QR PNG
decyph.me -e --url link.txt              # Save full URL to file
decyph.me -e --base64 data.txt           # Save base64 to file

# Multiple outputs simultaneously (encrypt only)
decyph.me -e --qr-code qr.png --url link.txt --base64 data.b64

# Encryption (piped - SECURE methods only)
cat file.txt | decyph.me -e --qr-code qr.png  # From file (SECURE)
pbpaste | decyph.me -e                        # From clipboard (SECURE)

# ⚠️ NEVER use echo with sensitive data:
# echo "Secret" | decyph.me -e  # ❌ INSECURE! Saves in shell history

# Decryption (interactive - prompts for data and password)
decyph.me -d
decyph.me -d --url encrypted.txt         # Read from URL file
decyph.me -d --base64 data.txt           # Read from base64 file
decyph.me -d --qr-code                   # Prompts for QR path
decyph.me -d --qr-code qr.png            # Scan QR → decrypt
decyph.me -d --clipboard                 # Clipboard QR → decrypt

# Decryption (piped - SECURE methods only)
cat encrypted.txt | decyph.me -d  # From file (SECURE)
pbpaste | decyph.me -d            # From clipboard (SECURE)

# ⚠️ NEVER use echo with encrypted data:
# echo "ARIIAYJo..." | decyph.me -d  # ❌ INSECURE! Saves in shell history

# QR code operations (no encryption)
decyph.me --encode-qr qr.png             # Plain text → QR PNG
decyph.me --encode-qr                    # Plain text → QR screen
decyph.me --decode-qr qr.png             # QR image → text
decyph.me --decode-qr                    # QR image → text (prompts for path)

# Advanced (custom QR styling)
decyph.me -e --qr-code qr.png -b 30 --fill blue --back yellow

# Quiet mode (suppress security warnings - use with caution!)
decyph.me -e -q

# === MINIMAL TOOL ===
# decrypt_qr_minimal.py - 7-line minimal decryption
python python-tools/decyph_minimal.py

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

1. **Python CLI Tools** (`python-tools/decyph.py` - unified tool, `decyph_minimal.py`)
   - Command-line interface for encryption/decryption, installed locally as `decyph.me`
   - Uses Python's `cryptography` library for crypto operations
   - Direct QR code generation with `qrcode[pil]`
   - QR code decoding from images with `opencv-python-headless` (no system deps)
   - **decyph.py** - All-in-one tool combining encryption, decryption, QR generation/decoding
   - **decyph_minimal.py** - 7-line minimal decryption tool
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