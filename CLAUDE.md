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

# Run main encryption tool (interactive)
python encrypt_qr.py

# Run minimal decryption tool
python decrypt_qr_minimal.py

# Convert files to QR codes
python file_to_qr.py
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

1. **Python CLI Tools** (`python-tools/encrypt_qr.py`, `decrypt_qr_minimal.py`, `file_to_qr.py`)
   - Command-line interface for encryption/decryption
   - Uses Python's `cryptography` library for crypto operations
   - Direct QR code generation with `qrcode[pil]`

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
- **Python**: `cryptography==41.0.7`, `qrcode[pil]==7.4.2`
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