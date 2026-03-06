# Python CLI Tools for decyph.me

Secure text encryption with QR code support from the command line.

## 🎯 Tools Overview

### **decyph.py** - Unified CLI Tool (Recommended)

All-in-one tool for encryption, decryption, and QR code operations:
- ✅ AES-256-GCM encryption with Scrypt KDF
- ✅ QR code generation (PNG + terminal ASCII)
- ✅ QR code decoding from images/clipboard
- ✅ Secure password prompts (never in command history!)
- ✅ Multiple input sources (file, stdin, QR image, clipboard)
- ✅ Multiple simultaneous outputs in encrypt mode
- ✅ Context-aware arguments (same flag adapts to encrypt/decrypt mode)
- ✅ Comprehensive security warnings (WiFi, keyloggers, air-gapped systems)
- ✅ Pipeline workflows (QR scan → decrypt in one command)

### **decrypt_qr_minimal.py** - Minimal Decryption

Ultra-compact 7-line decryption-only tool.

---

## 🔒 Security First

**Critical Security Features:**

- ✅ **Passwords NEVER accepted as command-line arguments** (prevents shell history leaks)
- ✅ **Encrypted data NEVER accepted as arguments** (prevents exposure)
- ✅ All sensitive data prompted securely via `getpass` or piped from stdin
- ✅ **Comprehensive security warnings** before sensitive operations:
  - Network security (WiFi, Bluetooth, internet connections)
  - Physical security (shoulder surfing, cameras)
  - System security (keyloggers, air-gapped systems, VM isolation)
  - Post-operation cleanup (history clearing, secure deletion)
- ✅ **Explicit confirmation before revealing decrypted plaintext**
  - Requires typing "YES" (all caps) to display plaintext
  - Dark navy blue text output (nearly invisible from shoulder surfing, readable when directly viewed)
  - Final chance to abort before sensitive data appears on screen
- ✅ AES-256-GCM authenticated encryption
- ✅ Strong password requirements (14+ chars, 3+ character classes)

### ⚠️ Shell History Dangers

**NEVER use `echo` with sensitive data!** Your shell (bash, zsh, etc.) saves every command to history files:
- `~/.bash_history` (bash)
- `~/.zsh_history` (zsh)
- `~/.history` (other shells)

**Insecure examples that leak data:**
```bash
# ❌ INSECURE - plaintext saved in history
echo "my secret password" | ./decyph.py -e

# ❌ INSECURE - encrypted data saved in history
echo "ARIIAYJo..." | ./decyph.py -d

# ❌ INSECURE - even passwords in commands
./decyph.py -e --password "MyPassword123"  # (Not supported, but shows why)
```

**Secure alternatives:**
```bash
# ✅ SECURE - pipe from file
cat secret.txt | ./decyph.py -e

# ✅ SECURE - pipe from clipboard
pbpaste | ./decyph.py -e

# ✅ SECURE - interactive prompt
./decyph.py -e  # Will prompt for input
```

**Why this matters:**
- History files are **plain text** and **persistent**
- Anyone with access to your account can read them
- Backups may preserve history files indefinitely
- Malware often harvests shell history for credentials

---

## 📦 Installation

### 1. Install Python Dependencies

```bash
cd python-tools
pip install -r requirements.txt
```

### 2. Install System Dependencies (for QR decoding)

**macOS:**
```bash
brew install zbar
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libzbar0
```

**Fedora:**
```bash
sudo dnf install zbar
```

---

## 🚀 Quick Start

### Encryption Examples

```bash
# Interactive: prompts for text and password
./decyph.py -e

# Encrypt and show QR on screen
./decyph.py -e --qr-code

# Encrypt and save as QR PNG
./decyph.py -e --qr-code qr.png

# Save URL to file
./decyph.py -e --url output.txt

# Save base64 to file
./decyph.py -e --base64 data.txt

# Multiple outputs simultaneously (QR PNG + URL file + base64 to screen)
./decyph.py -e --qr-code qr.png --url output.txt --base64

# Pipe from file (SECURE)
cat message.txt | ./decyph.py -e

# Pipe from clipboard (SECURE)
pbpaste | ./decyph.py -e --qr-code qr.png

# ⚠️ NEVER DO THIS - INSECURE!
# echo "Secret message" | ./decyph.py -e
# ❌ This saves "Secret message" in your shell history!
```

### Decryption Examples

```bash
# Interactive: prompts for encrypted data and password
./decyph.py -d

# Read encrypted data from URL file
./decyph.py -d --url encrypted.txt

# Read encrypted data from base64 file
./decyph.py -d --base64 data.txt

# Scan QR and decrypt (prompts for image path)
./decyph.py -d --qr-code

# Decrypt from QR image file (supports PNG, JPEG, WEBP, etc.)
./decyph.py -d --qr-code qr.png
./decyph.py -d --qr-code photo.jpg      # JPEG works!
./decyph.py -d --qr-code scan.jpeg      # Any image format

# Decrypt from clipboard QR
./decyph.py -d --clipboard

# Pipe from file (SECURE)
cat encrypted.txt | ./decyph.py -d

# Pipe from clipboard (SECURE)
pbpaste | ./decyph.py -d

# ⚠️ NEVER DO THIS - INSECURE!
# echo "ARIIAYJo..." | ./decyph.py -d
# ❌ This saves encrypted data in your shell history!
```

### QR Code Operations

```bash
# Encode text as QR (no encryption), save as PNG
./decyph.py --encode-qr qr.png

# Encode text as QR, show on screen
./decyph.py --encode-qr

# Decode QR to text (no decryption) - supports PNG, JPEG, WEBP, etc.
./decyph.py --decode-qr qr.png
./decyph.py --decode-qr photo.jpg              # JPEG works too!
./decyph.py --decode-qr scan.jpeg              # Any image format

# Decode QR (prompts for image path)
./decyph.py --decode-qr

# Custom colored QR code
./decyph.py --encode-qr qr.png --fill blue --back yellow
```

---

## 📖 Command Reference

### Modes

| Flag | Description |
|------|-------------|
| `-e, --encrypt` | Encrypt text with password |
| `-d, --decrypt` | Decrypt encrypted data |
| `--encode-qr [FILE]` | Encode QR code (no encryption). FILE=save PNG, empty=screen |
| `--decode-qr [FILE]` | Decode QR code (no decryption). FILE=image path, empty=prompt |

### Context-Aware Input/Output Options

These arguments adapt their behavior based on the mode:

| Flag | Encrypt Mode (Output) | Decrypt Mode (Input) |
|------|----------------------|---------------------|
| `--qr-code [FILE]` | Save QR PNG (file) or show on screen (no file) | Read from QR image (file) or prompt for path (no file) |
| `--url [FILE]` | Save full URL (file) or show on screen (no file) | Read from URL file or prompt for encrypted data |
| `--base64 [FILE]` | Save base64 (file) or show on screen (no file) | Read from base64 file or prompt for encrypted data |
| `--clipboard` | Copy to clipboard | Read QR from clipboard |

**Important Notes:**
- **Encrypt mode**: Multiple outputs can be specified simultaneously (e.g., `--qr-code qr.png --url out.txt --base64`)
- **Decrypt mode**: Only ONE input source allowed (will error if multiple specified)
- **Supported QR image formats**: PNG, JPEG (.jpg, .jpeg), WEBP, GIF, BMP, TIFF, and 50+ other formats (via Pillow)
- Text and encrypted data are never accepted as command-line arguments for security
- All sensitive data prompted interactively or piped from stdin

### General Options

| Flag | Description |
|------|-------------|
| `-q, --quiet` | Suppress security warnings (use with caution!) |
| `--encoding ENC` | File encoding (default: utf-8) |

### QR Code Parameters

| Flag | Description |
|------|-------------|
| `-b, --box-size N` | Box size in pixels (default: 50) |
| `-r, --border N` | Border size in boxes (default: 4) |
| `--error-correction LEVEL` | L/M/Q/H (default: H) |
| `--fill COLOR` | Foreground color (default: black) |
| `--back COLOR` | Background color (default: white) |

---

## 🔐 Security Details

### Password Requirements

Passwords must meet these criteria:
- **Minimum 14 characters**
- **At least 3 of the following:**
  - Lowercase letters (a-z)
  - Uppercase letters (A-Z)
  - Digits (0-9)
  - Special characters

### Encryption Scheme

- **Algorithm:** AES-256-GCM (Authenticated Encryption)
- **Key Derivation:** Scrypt (N=2^18, r=8, p=1)
- **Salt:** 16 bytes (random)
- **Nonce:** 12 bytes (random)
- **Format:** V1 with future-proof header
- **Encoding:** Base64 URL-safe

### Cross-Platform Compatibility

Fully compatible with:
- ✅ Python CLI tools (this directory)
- ✅ Web application ([decyph.me](https://decyph.me))
- ✅ JavaScript implementation

Encrypt with CLI, decrypt with web app, or vice versa!

---

## 💡 Usage Examples

### Example 1: Secure File Sharing

```bash
# Alice: Encrypt document and generate QR
./decyph.py -e --url confidential.pdf --qr-code share.png
# (prompted for password, reads plaintext from file, saves QR to PNG)

# Send share.png to Bob via any channel

# Bob: Scan QR and decrypt
./decyph.py -d --qr-code share.png
# (prompted for password)
```

### Example 2: Password Backup

```bash
# Generate QR for master password
./decyph.py -e --qr-code backup.png
# Input: MyMasterPassword2024!
# Prompted: encryption password

# Print and store physically
# Years later, scan to recover:
./decyph.py -d --qr-code backup.png
```

### Example 3: Secure Piped Workflows

```bash
# Encrypt from clipboard (SECURE)
pbpaste | ./decyph.py -e --qr-code qr.png

# Encrypt from file (SECURE)
cat data.txt | ./decyph.py -e --qr-code qr.png

# Decrypt and save to file (SECURE)
./decyph.py -d --qr-code qr.png -q > decrypted.txt

# Chain operations (SECURE)
cat data.txt | ./decyph.py -e | ./decyph.py --encode-qr --qr-code qr.png

# ⚠️ INSECURE EXAMPLES - NEVER USE:
# echo "Secret" | ./decyph.py -e          # ❌ "Secret" in shell history
# echo "password123" | ./decyph.py -e     # ❌ Password exposed in history
# Always use files or clipboard, NEVER echo with sensitive data!
```

### Example 4: Batch Processing

```bash
# Encrypt multiple files
for file in *.txt; do
  ./decyph.py -e --url "$file" --qr-code "${file%.txt}-qr.png"
done

# Note: Password will be prompted for each file
```

### Example 5: Multiple Outputs

```bash
# Save encrypted data in all formats simultaneously
./decyph.py -e --qr-code qr.png --url link.txt --base64 data.b64
# Creates: qr.png (QR image), link.txt (full URL), data.b64 (base64 only)

# Show all outputs on screen
./decyph.py -e --qr-code --url --base64
# Displays: QR in terminal, full URL, and base64 data
```

---

## 🛠️ Troubleshooting

### QR Decoding Errors

**Error:** "QR decoding not available"

**Solution:**
```bash
# Install zbar library (see Installation section)
# Install Python packages
pip install pillow pyzbar
```

**Error:** "No QR code found in image"

**Solutions:**
- Ensure image is clear and well-lit
- Use higher error correction when generating: `-e H`
- Try rescanning with better camera/scanner

### Permission Errors

```bash
# Make script executable
chmod +x decyph.py
```

### Import Errors

```bash
# Ensure dependencies installed
pip install -r requirements.txt
```

### QR Code Image Format Questions

**Q: Does it support JPEG/JPG images?**
✅ **Yes!** The tool supports JPEG, JPG, and 50+ other image formats including:
- **Common**: PNG, JPEG (.jpg, .jpeg, .jpe), GIF, BMP, WEBP
- **Professional**: TIFF, JPEG 2000 (.jp2), PSD (Photoshop)
- **Others**: ICO, PPM, PGM, PCX, TGA, and many more

The tool uses Pillow (PIL) which has extensive format support. You can use any image containing a QR code.

**Q: Which format is best for QR codes?**
PNG is recommended because:
- Lossless compression (no quality degradation)
- Best for sharp edges and high contrast (QR codes)
- Smaller file size than BMP
- JPEG uses lossy compression which can make QR codes harder to scan

---

## 📋 Output Format Examples

### Encryption Output (Default - No Output Flags)

```
======================================================================
Encryption Successful!
======================================================================

⚠️  SECURITY WARNING: Encrypted data will be displayed on screen. Ensure no one is watching!

Encrypted Data (Base64):
ARIIAYJoSB_TuzVpcpMO_tD_zc8fcx58DJ2f0K8nbog-...

Shareable Link (Full URL):
https://decyph.me/#ARIIAYJoSB_TuzVpcpMO_tD_zc8fcx58DJ2f...
```

### Encryption with QR on Screen (--qr-code)

```
⚠️  SECURITY WARNING: QR code will be displayed on screen. Ensure no one is watching!

QR Code (Terminal):
 ▄▄▄▄▄▄▄   ▄▄▄▄▄▄ ▄ ▄  ▄   ▄  ▄▄▄▄ ▄▄▄▄▄▄▄
 █ ▄▄▄ █ █▄▄▄▄█▀▀█ █▄▀ ██▀▀ █▄▄█▄█ █ ▄▄▄ █
 ...
```

### Encryption with PNG (--qr-code qr.png)

```
⚠️  SECURITY WARNING: QR code will be saved to disk: qr.png. This leaves a permanent trace!

QR Code saved to: qr.png
  Version: 11
  Image size: 3450x3450 pixels
```

### Decryption Output (with confirmation)

```
⚠️  SECURITY WARNING: Decrypted plaintext will be displayed on screen...

======================================================================
⚠️  FINAL CONFIRMATION BEFORE REVEALING PLAINTEXT
======================================================================

Decryption was SUCCESSFUL. The plaintext is ready to display.

BEFORE REVEALING:
- Ensure no one is watching your screen
- Ensure no screen recording software is running
- Consider redirecting output to a file instead: decyph.py -d -q > output.txt

This is your LAST CHANCE to abort before plaintext appears on screen.

⚠️  Type 'YES' (all caps) to reveal plaintext, or Ctrl+C to abort: YES

======================================================================
Decryption Successful!
======================================================================

Decrypted Text (in dark blue for security - harder to see from shoulder surfing):

======================================================================
[Text displayed in DARK NAVY BLUE - nearly invisible from distance]
======================================================================

⚠️  Remember to clear this from your terminal history!
    Clear now: history -c && history -w
```

### Quiet Mode (-q)

Suppresses warnings and confirmation prompts. Outputs in dark navy blue text:
```
[Decrypted text in dark navy blue - still hard to see from distance]
```

Use for piping to files:
```bash
./decyph.py -d -q > output.txt  # No prompts, just output
```

---

## 🔄 Default Behaviors

### No Output Flags Specified

When encrypting **without** any output flags (`--qr-code`, `--url`, `--base64`), the tool displays both formats on screen:
- Base64 encrypted data
- Full URL (https://decyph.me/#...)

### Context-Aware Arguments

The same argument adapts based on mode:
- **Encrypt mode**: Arguments specify OUTPUT format and destination
- **Decrypt mode**: Arguments specify INPUT source

### Security Warnings

By default, the tool shows comprehensive security warnings:
- Before password input (WiFi, keyloggers, air-gapped systems)
- When displaying sensitive data on screen
- When saving data to disk

Use `-q` (quiet mode) to suppress these warnings if you understand the risks.

---

## 📚 Additional Resources

- **Legacy Tools:** See [LEGACY_TOOLS.md](LEGACY_TOOLS.md) for old tool documentation
- **Web App:** [decyph.me](https://decyph.me)
- **Source Code:** Parent repository

---

## ⚡ Tips & Best Practices

1. **NEVER use `echo` with sensitive data** - it saves to shell history permanently!
   - ❌ `echo "secret" | ./decyph.py -e`
   - ✅ `cat file.txt | ./decyph.py -e` or `pbpaste | ./decyph.py -e`
2. **Use interactive mode when possible** - prompts are more secure than pipes
3. **Read the confirmation prompts carefully** - they give you a last chance to ensure privacy
4. **Dark blue text is intentional** - decrypted plaintext displays in dark navy blue (nearly invisible from shoulder surfing, readable up close)
5. **Use high error correction** (default is H) for printed QR codes
6. **Store passwords in password manager**, not shell scripts or environment variables
7. **Test QR scannability** before relying on them for backups
8. **Use --qr-code** without filename to preview QR on screen before saving
9. **Use multiple outputs** in encrypt mode to save all formats at once
10. **Always read security warnings** unless you're confident in your environment
11. **Consider air-gapped systems** for highly sensitive operations
12. **Use quiet mode (-q) carefully** - security warnings and confirmations exist for a reason
13. **Clear shell history after operations:** `history -c && history -w`
14. **Verify shell history is empty:** `history | tail` (should be empty after clearing)

---

## 📄 License

MIT License
