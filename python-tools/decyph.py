#!/usr/bin/env python3
"""
decyph.py - Unified CLI tool for encryption/decryption with QR code support

Features:
  - Encrypt/decrypt text with AES-256-GCM + Scrypt KDF
  - Generate QR codes (PNG or terminal ASCII)
  - Decode QR codes from images or clipboard
  - Multiple input sources: text, file, stdin, QR image, clipboard
  - Flexible output: terminal, file, QR code (PNG/ASCII), clipboard
  - Pipeline workflows: QR → decode → decrypt in one command
"""

import os
import sys
import base64
import getpass
import secrets
import argparse
import unicodedata as u
import urllib.parse as up
from pathlib import Path
from typing import Optional, Tuple

# Cryptography
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# QR code generation
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

# QR code decoding (optional dependencies)
try:
    import cv2
    from PIL import Image
    QR_DECODE_AVAILABLE = True
except ImportError:
    QR_DECODE_AVAILABLE = False

# Clipboard support (optional)
try:
    from PIL import ImageGrab
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


# ============================================================================
# Crypto Configuration
# ============================================================================
VER = 1                 # Format version
LOGN, R, P = 18, 8, 1   # Scrypt: N=2^18 (~256 MiB), r=8, p=1
KEYLEN = 32             # AES-256-GCM
SALTLEN = 16
NONCELEN = 12
MIN_PW_LEN = 14
BASE_URL = "https://decyph.me/#"


# ============================================================================
# Crypto Functions
# ============================================================================
def _hdr_bytes():
    return bytes([VER, LOGN, R, P])


def _parse_hdr(h):
    if len(h) != 4 or h[0] != VER:
        raise ValueError("bad header/version")
    return (1 << h[1]), h[2], h[3]  # N, r, p


def _norm_pwd(pw: str) -> bytes:
    return u.normalize("NFC", pw).encode("utf-8")


def _kdf_scrypt(pw_bytes: bytes, salt: bytes, N: int, r: int, p: int, ln: int) -> bytes:
    return Scrypt(salt=salt, length=ln, n=N, r=r, p=p).derive(pw_bytes)


def _strong_pw(p: str) -> bool:
    """Check if password meets minimum strength requirements."""
    if len(p) < MIN_PW_LEN:
        return False
    classes = sum(
        any(getattr(c, "isascii")() and test(c) for c in p)
        for test in (str.islower, str.isupper, str.isdigit)
    )
    specials = any(not c.isalnum() for c in p)
    return classes + (1 if specials else 0) >= 3


def encrypt(plaintext: str, password: str) -> str:
    """Encrypt plaintext with password, return base64 encoded ciphertext."""
    salt, nonce = os.urandom(SALTLEN), os.urandom(NONCELEN)
    key = _kdf_scrypt(_norm_pwd(password), salt, 1 << LOGN, R, P, KEYLEN)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), _hdr_bytes() + salt + nonce)
    blob = _hdr_bytes() + salt + nonce + ct
    return base64.urlsafe_b64encode(blob).decode("ascii")


def _extract_b64(s: str) -> str:
    """Extract base64 from raw string or URL."""
    if s.startswith("http://") or s.startswith("https://"):
        s = up.unquote(s)
        i = s.find("#")
        if i != -1:
            return s[i + 1:]
    return s


def decrypt(b64_or_url: str, password: str) -> str:
    """Decrypt base64 or URL encoded ciphertext with password."""
    raw_b64 = _extract_b64(b64_or_url)
    raw = base64.urlsafe_b64decode(raw_b64)
    if len(raw) < 4 + SALTLEN + NONCELEN:
        raise ValueError("truncated data")
    hdr, rest = raw[:4], raw[4:]
    N, r, p = _parse_hdr(hdr)
    salt = rest[:SALTLEN]
    nonce = rest[SALTLEN:SALTLEN + NONCELEN]
    ct = rest[SALTLEN + NONCELEN:]
    key = _kdf_scrypt(_norm_pwd(password), salt, N, r, p, KEYLEN)
    pt = AESGCM(key).decrypt(nonce, ct, hdr + salt + nonce)
    return pt.decode("utf-8")


# ============================================================================
# QR Code Generation
# ============================================================================
def generate_qr_console(data: str):
    """Display QR code as ASCII art in terminal."""
    qr = qrcode.QRCode(
        error_correction=ERROR_CORRECT_L,
        box_size=1,
        border=1
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii()


def generate_qr_png(
    data: str,
    output: str,
    box_size: int = 50,
    border: int = 4,
    error_correction: str = 'H',
    fill_color: str = 'black',
    back_color: str = 'white',
) -> Tuple[str, int, Tuple[int, int]]:
    """
    Generate QR code and save as PNG.

    Returns:
        Tuple of (output_path, qr_version, image_size)
    """
    error_correction_map = {
        'L': ERROR_CORRECT_L,
        'M': ERROR_CORRECT_M,
        'Q': ERROR_CORRECT_Q,
        'H': ERROR_CORRECT_H,
    }

    ec_level = error_correction_map.get(error_correction.upper())
    if ec_level is None:
        raise ValueError(f"Invalid error correction level: {error_correction}")

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=box_size,
        border=border,
    )

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    img.save(output)

    return output, qr.version, img.size


# ============================================================================
# QR Code Decoding
# ============================================================================
def decode_qr_from_file(image_path: str) -> str:
    """Decode QR code from image file."""
    if not QR_DECODE_AVAILABLE:
        raise RuntimeError(
            "QR decoding not available. Install: pip install opencv-python-headless"
        )

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Failed to open image: {image_path}")

    data, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    if not data:
        raise ValueError("No QR code found in the image")

    return data


def decode_qr_from_clipboard() -> str:
    """Decode QR code from clipboard image."""
    if not CLIPBOARD_AVAILABLE:
        raise RuntimeError("Clipboard support not available (PIL.ImageGrab)")

    if not QR_DECODE_AVAILABLE:
        raise RuntimeError("QR decoding not available (opencv-python-headless)")

    img = ImageGrab.grabclipboard()

    if img is None:
        raise ValueError("No image found in clipboard")

    if not isinstance(img, Image.Image):
        raise ValueError("Clipboard content is not an image")

    import numpy as np
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    data, _, _ = cv2.QRCodeDetector().detectAndDecode(cv_img)
    if not data:
        raise ValueError("No QR code found in clipboard image")

    return data


# ============================================================================
# Input Handling
# ============================================================================
def get_input_data(args, mode: str, prompt_message: str = None) -> str:
    """
    Get input data from various sources based on mode and arguments.

    Args:
        args: Parsed command-line arguments
        mode: 'encrypt' or 'decrypt'
        prompt_message: Message to show for interactive input

    Returns:
        Input data as string
    """
    # Count how many input sources are specified (for decrypt mode validation)
    input_sources = []
    if args.qr_code is not None:
        input_sources.append('--qr-code')
    if args.url is not None:
        input_sources.append('--url')
    if args.base64 is not None:
        input_sources.append('--base64')
    if args.clipboard:
        input_sources.append('--clipboard')

    # For decrypt mode, only allow one input source
    if mode == 'decrypt' and len(input_sources) > 1:
        raise ValueError(
            f"Cannot use multiple input sources simultaneously: {', '.join(input_sources)}. "
            "Please specify only one: --qr-code, --url, --base64, or --clipboard"
        )

    # Handle QR code input (decrypt mode) or link file input
    if args.qr_code is not None:
        if mode == 'decrypt':
            # QR code as input
            if args.qr_code == '':
                # Prompt for QR code file path
                qr_path = input("Enter QR code image path: ").strip()
                if not qr_path:
                    raise ValueError("No QR code path provided")
                return decode_qr_from_file(qr_path)
            else:
                # QR code file specified
                return decode_qr_from_file(args.qr_code)

    # Handle URL file input
    if args.url is not None:
        if mode == 'decrypt' or mode == 'encode_qr':
            if args.url == '':
                url_path = input("Enter URL/data file path: ").strip()
                if not url_path:
                    raise ValueError("No file path provided")
                file_path = Path(url_path)
            else:
                file_path = Path(args.url)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            try:
                return file_path.read_text(encoding=args.encoding)
            except UnicodeDecodeError as e:
                raise ValueError(f"Cannot decode file with {args.encoding} encoding: {e}")

    # Handle base64 file input
    if args.base64 is not None:
        if mode == 'decrypt' or mode == 'encode_qr':
            if args.base64 == '':
                b64_path = input("Enter base64 data file path: ").strip()
                if not b64_path:
                    raise ValueError("No file path provided")
                file_path = Path(b64_path)
            else:
                file_path = Path(args.base64)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            try:
                return file_path.read_text(encoding=args.encoding)
            except UnicodeDecodeError as e:
                raise ValueError(f"Cannot decode file with {args.encoding} encoding: {e}")

    # Handle clipboard
    if args.clipboard:
        if mode == 'decrypt':
            # Read QR from clipboard
            try:
                return decode_qr_from_clipboard()
            except RuntimeError as e:
                raise ValueError(f"Clipboard QR decoding failed: {e}")

    # Check if stdin has data (piped)
    if not sys.stdin.isatty():
        return sys.stdin.read()

    # Interactive prompt
    if prompt_message:
        print(prompt_message, file=sys.stderr)
        print("(Ctrl+D or Ctrl+Z on new line when done):", file=sys.stderr)
        return sys.stdin.read()

    # No input source specified
    return None


def show_security_warning(message: str, quiet: bool = False):
    """Display security warning unless quiet mode."""
    if not quiet:
        print(f"\n⚠️  SECURITY WARNING: {message}", file=sys.stderr)


def show_password_security_notice(quiet: bool = False):
    """Show comprehensive security notice before password input."""
    if quiet:
        return

    print("\n" + "="*70, file=sys.stderr)
    print("⚠️  SECURITY NOTICE - READ CAREFULLY", file=sys.stderr)
    print("="*70, file=sys.stderr)
    print("""
BEFORE ENTERING YOUR PASSWORD, ENSURE:

1. NETWORK SECURITY:
   - WiFi is TURNED OFF (use ethernet or offline entirely)
   - No active internet connections
   - Bluetooth is DISABLED

2. PHYSICAL SECURITY:
   - No one is watching your screen (shoulder surfing)
   - No cameras pointing at your keyboard
   - You are in a private, secure location

3. SYSTEM SECURITY MEASURES:
   - Use computer that was obtained in a way that is safe, trustworthy and untampered 
   - The computer should only be accessible to you (physically, at all times)
   - The OS should be freshly installed, use penultimate (or at least previous) LTS release with all most recent security patches installed
   - Consider using air-gapped computer (never connected to internet) inside faraday cage
   - Beware of keyloggers (hardware and software)
   - Use a script within dedicated VM environment without network access
   - Destroy VM environment after operation if handling highly sensitive data

4. POST-OPERATION:
   - Clear bash history: history -c && history -w
   - Consider secure-deleting temporary files
   - For extreme paranoia: physically destroy the hard drive and computer after operation

❌ Press Ctrl+C to abort if you need to improve your security setup first.
""", file=sys.stderr)
    input("⚠️  Press Enter when ready to input your password... ")
    print(file=sys.stderr)


def get_password(confirm: bool = False, quiet: bool = False) -> str:
    """Prompt user for password securely with security warnings."""
    show_password_security_notice(quiet)

    pw1 = getpass.getpass("Enter password: ")

    if confirm:
        pw2 = getpass.getpass("Confirm password: ")
        if not secrets.compare_digest(pw1, pw2):
            raise ValueError("Passwords do not match")

    return pw1


# ============================================================================
# Output Handling
# ============================================================================
def output_encryption_result(encrypted_b64: str, args):
    """
    Output encryption results based on arguments (context-aware).

    Supports multiple simultaneous outputs:
    - --qr-code: Save PNG or show on screen
    - --url: Save full URL to file or show on screen
    - --base64: Save base64 to file or show on screen
    - --clipboard: Copy to clipboard
    - Default (none specified): Show all on screen
    """
    full_url = BASE_URL + encrypted_b64
    base64_only = encrypted_b64

    # Check if any output specified
    has_output = any([
        args.qr_code is not None,
        args.url is not None,
        args.base64 is not None,
        args.clipboard
    ])

    outputs_done = []

    # Handle QR code output
    if args.qr_code is not None:
        if args.qr_code == '':
            # Show QR on screen
            show_security_warning(
                "QR code will be displayed on screen. Ensure no one is watching!",
                args.quiet
            )
            if not args.quiet:
                print("\nQR Code (Screen):")
            generate_qr_console(full_url)
            outputs_done.append("QR on screen")
        else:
            # Save QR as PNG
            show_security_warning(
                f"QR code will be saved to disk: {args.qr_code}. "
                "This leaves a permanent trace! Consider secure deletion later.",
                args.quiet
            )
            output_path, qr_version, img_size = generate_qr_png(
                data=full_url,
                output=args.qr_code,
                box_size=args.box_size,
                border=args.border,
                error_correction=args.error_correction,
                fill_color=args.fill,
                back_color=args.back,
            )

            if not args.quiet:
                print(f"\n✓ QR Code saved to: {output_path}")
                print(f"  Version: {qr_version}")
                print(f"  Image size: {img_size[0]}x{img_size[1]} pixels")
            outputs_done.append(f"QR → {output_path}")

    # Handle URL output
    if args.url is not None:
        if args.url == '':
            # Show URL on screen
            show_security_warning(
                "Full URL will be displayed on screen. Anyone seeing it can decrypt your data!",
                args.quiet
            )
            if not args.quiet:
                print("\nFull URL:")
            print(full_url)
            outputs_done.append("URL on screen")
        else:
            # Save URL to file
            show_security_warning(
                f"Full URL will be saved to disk: {args.url}. "
                "This is highly sensitive! Consider encryption or secure deletion.",
                args.quiet
            )
            Path(args.url).write_text(full_url + '\n', encoding=args.encoding)
            if not args.quiet:
                print(f"\n✓ Full URL saved to: {args.url}")
            outputs_done.append(f"URL → {args.url}")

    # Handle base64 output
    if args.base64 is not None:
        if args.base64 == '':
            # Show base64 on screen
            show_security_warning(
                "Encrypted base64 will be displayed on screen. Ensure no one is watching!",
                args.quiet
            )
            if not args.quiet:
                print("\nEncrypted Data (Base64):")
            print(base64_only)
            outputs_done.append("Base64 on screen")
        else:
            # Save base64 to file
            show_security_warning(
                f"Encrypted data will be saved to disk: {args.base64}. "
                "Consider secure deletion after use.",
                args.quiet
            )
            Path(args.base64).write_text(base64_only + '\n', encoding=args.encoding)
            if not args.quiet:
                print(f"\n✓ Base64 saved to: {args.base64}")
            outputs_done.append(f"Base64 → {args.base64}")

    # Handle clipboard output
    if args.clipboard:
        # TODO: Implement clipboard write functionality
        show_security_warning(
            "Clipboard write not yet implemented. Data shown on screen instead.",
            args.quiet
        )
        if not args.quiet:
            print("\nEncrypted Data (for clipboard):")
        print(encrypted_b64)
        outputs_done.append("Clipboard (not implemented)")

    # Default: Show everything on screen if no output specified
    if not has_output:
        show_security_warning(
            "Encrypted data and URL will be displayed on screen. Ensure privacy!",
            args.quiet
        )
        if not args.quiet:
            print("\n" + "="*70)
            print("Encryption Successful!")
            print("="*70)
            print("\nEncrypted Data (Base64):")
            print(base64_only)
            print("\nShareable Link (Full URL):")
            print(full_url)
            print("\nQR Code:")
            generate_qr_console(full_url)
        else:
            print(base64_only)

    # Summary
    if outputs_done and not args.quiet:
        print(f"\n✓ Outputs generated: {', '.join(outputs_done)}")


def output_decryption_result(decrypted_text: str, args):
    """Output decryption results with security warnings and confirmation."""
    # First warning
    show_security_warning(
        "Decrypted plaintext will be displayed on screen. "
        "Ensure no one is watching! Consider clearing terminal history after.",
        args.quiet
    )

    # Ask for explicit confirmation before revealing plaintext (unless quiet mode)
    if not args.quiet:
        print("\n" + "="*70, file=sys.stderr)
        print("⚠️  FINAL CONFIRMATION BEFORE REVEALING PLAINTEXT", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print("""
Decryption was SUCCESSFUL. The plaintext is ready to display.

BEFORE REVEALING:
- Ensure no one is watching your screen
- Ensure no screen recording software is running
- Consider redirecting output to a file instead: decyph.py -d -q > output.txt

This is your LAST CHANCE to abort before plaintext appears on screen.
""", file=sys.stderr)

        response = input("⚠️  Type 'YES' (all caps) to reveal plaintext, or Ctrl+C to abort: ")
        if response.strip() != "YES":
            print("\nAborted. Plaintext was NOT displayed.", file=sys.stderr)
            print("Hint: Use -q flag to redirect to file: decyph.py -d -q > output.txt", file=sys.stderr)
            sys.exit(0)

    # ANSI color codes - dark blue/navy text (much harder to see at a glance for shoulder surfing protection)
    # Using 256-color mode for darker blue: \033[38;5;Nm where N is the color code
    # Color 18 = dark blue, Color 17 = navy blue, Color 4 = standard blue
    DARK_BLUE = '\033[38;5;18m'  # Very dark blue, nearly invisible from distance
    RESET = '\033[0m'

    if args.quiet:
        # In quiet mode, still use dark blue for security
        print(f"{DARK_BLUE}{decrypted_text}{RESET}")
    else:
        print("\n" + "="*70)
        print("Decryption Successful!")
        print("="*70)
        print("\nDecrypted Text (in dark blue for security - harder to see from shoulder surfing):")
        print("\n" + "="*70)
        print(f"{DARK_BLUE}{decrypted_text}{RESET}")
        print("="*70)
        print("\n⚠️  Remember to clear this from your terminal history!")
        print("    Clear now: history -c && history -w")


# ============================================================================
# Main Command Modes
# ============================================================================
def cmd_encrypt(args):
    """Encryption mode."""
    # Get input (context: encrypt mode, may read from --url/--base64 file)
    plaintext = get_input_data(args, mode='encrypt', prompt_message="Enter text to encrypt:")
    if not plaintext:
        raise ValueError("No input data provided")

    plaintext = plaintext.strip()
    if not plaintext:
        raise ValueError("No input data provided")

    # Get password (always prompt, never from args) with security warnings
    password = get_password(confirm=True, quiet=args.quiet)

    # Validate password
    if not _strong_pw(password):
        raise ValueError(
            f"Password too weak (min {MIN_PW_LEN} chars, 3+ character classes: "
            "lowercase, uppercase, digits, special characters)"
        )

    # Encrypt
    encrypted_b64 = encrypt(plaintext, password)

    # Output results (context-aware, multiple outputs supported)
    output_encryption_result(encrypted_b64, args)


def cmd_decrypt(args):
    """Decryption mode."""
    # Get encrypted data (context: decrypt mode, validates mutual exclusivity)
    encrypted_data = get_input_data(args, mode='decrypt', prompt_message="Enter encrypted data (base64 or URL):")
    if not encrypted_data:
        raise ValueError("No encrypted data provided")

    encrypted_data = encrypted_data.strip()
    if not encrypted_data:
        raise ValueError("No encrypted data provided")

    # Get password (always prompt, never from args) with security warnings
    password = get_password(confirm=False, quiet=args.quiet)

    # Decrypt
    try:
        decrypted_text = decrypt(encrypted_data, password)
    except Exception as e:
        raise ValueError(f"Decryption failed (wrong password or corrupted data): {e}")

    # Output results with security warnings
    output_decryption_result(decrypted_text, args)


def cmd_encode_qr(args):
    """QR code encoding only (no encryption)."""
    # Get input (may read from --url or --base64 file)
    data = get_input_data(args, mode='encode_qr', prompt_message="Enter text for QR code:")
    if not data:
        raise ValueError("No input data provided")

    data = data.strip()
    if not data:
        raise ValueError("No input data provided")

    # Output QR code using --encode-qr argument directly
    if args.encode_qr == '':
        # Show terminal QR (no filename provided)
        if not args.quiet:
            print("QR Code:")
        generate_qr_console(data)
    else:
        # Save PNG (filename provided)
        output_path, qr_version, img_size = generate_qr_png(
            data=data,
            output=args.encode_qr,
            box_size=args.box_size,
            border=args.border,
            error_correction=args.error_correction,
            fill_color=args.fill,
            back_color=args.back,
        )

        if not args.quiet:
            print(f"QR code saved to: {output_path}")
            print(f"  Version: {qr_version}")
            print(f"  Image size: {img_size[0]}x{img_size[1]} pixels")


def cmd_decode_qr(args):
    """Decode QR code only (no decryption)."""
    # Use --decode-qr argument directly
    if args.decode_qr == '':
        # Prompt for QR file path (no filename provided)
        qr_path = input("Enter QR code image path: ").strip()
        if not qr_path:
            raise ValueError("No QR code path provided")
        decoded_text = decode_qr_from_file(qr_path)
    else:
        # Decode from specified file
        decoded_text = decode_qr_from_file(args.decode_qr)

    if args.quiet:
        print(decoded_text)
    else:
        print("Decoded QR Code:")
        print(decoded_text)


# ============================================================================
# CLI Argument Parser
# ============================================================================
def create_parser():
    parser = argparse.ArgumentParser(
        prog='decyph.py',
        description='Unified encryption/decryption tool with QR code support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
SECURITY NOTE:
  Passwords should NEVER passed via command-line to prevent shell
  history leaks. Always prompted securely or piped from stdin.

DESIGN:
  Arguments are context-aware based on mode (-e/-d):
  - --qr-code, --url, --base64: OUTPUT in encrypt, INPUT in decrypt
  - --clipboard: WRITE in encrypt mode, READ in decrypt mode
  - Multiple outputs can be specified simultaneously in encrypt mode

EXAMPLES:

Encryption (interactive):
  %(prog)s -e                              # Prompts for text and password
  %(prog)s -e --url data.txt               # Read from file, prompts password
  %(prog)s -e --qr-code                    # Prompts text, shows QR on screen
  %(prog)s -e --qr-code qr.png             # Prompts text, saves QR as PNG
  %(prog)s -e --qr-code qr.png --url out.txt  # Save both QR and URL
  %(prog)s -e --base64 --qr-code --url     # Output all three to screen

Encryption (piped - SECURE):
  cat file.txt | %(prog)s -e --qr-code qr.png     # Pipe from FILE (secure)
  pbpaste | %(prog)s -e --qr-code qr.png          # Pipe from clipboard (secure)

  ⚠️  DANGEROUS - DO NOT USE:
  echo "Secret" | %(prog)s -e    # ❌ INSECURE! "Secret" saved in shell history!

Decryption (interactive):
  %(prog)s -d                              # Prompts for encrypted data and password
  %(prog)s -d --url data.txt               # Read encrypted data from file
  %(prog)s -d --base64 data.txt            # Read base64 from file
  %(prog)s -d --qr-code                    # Prompts for QR image path
  %(prog)s -d --qr-code qr.png             # Decode QR from file
  %(prog)s -d --clipboard                  # Read QR from clipboard

Decryption (piped - SECURE):
  cat encrypted.txt | %(prog)s -d          # Pipe from FILE (secure)
  pbpaste | %(prog)s -d                    # Pipe from clipboard (secure)

  ⚠️  DANGEROUS - DO NOT USE:
  echo "ARIIAYJo..." | %(prog)s -d   # ❌ INSECURE! Encrypted data in shell history!

QR Code Operations (no encryption):
  %(prog)s --encode-qr qr.png              # Plain text → QR PNG
  %(prog)s --encode-qr                     # Plain text → QR screen
  %(prog)s --decode-qr qr.png              # QR image → text
  %(prog)s --decode-qr                     # QR image → text (prompts for path)

Advanced:
  %(prog)s -e --qr-code qr.png -b 30 --fill blue  # Custom QR styling
"""
    )

    # ========== Mode Selection ==========
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '-e', '--encrypt',
        action='store_true',
        help='Encrypt mode'
    )
    mode_group.add_argument(
        '-d', '--decrypt',
        action='store_true',
        help='Decrypt mode'
    )
    mode_group.add_argument(
        '--encode-qr',
        nargs='?',
        const='',
        type=str,
        help='Encode QR code only (no encryption). FILE=save PNG, empty=screen',
        metavar='FILE'
    )
    mode_group.add_argument(
        '--decode-qr',
        nargs='?',
        const='',
        type=str,
        help='Decode QR code only (no decryption). FILE=image path, empty=prompt',
        metavar='FILE'
    )

    # ========== Context-Aware I/O Arguments ==========
    io_group = parser.add_argument_group('Input/Output (context-aware based on mode)')
    io_group.add_argument(
        '--qr-code',
        nargs='?',
        const='',
        type=str,
        help='Encrypt: output QR (FILE=save PNG, empty=screen). Decrypt: input QR (FILE=read PNG, empty=prompt path)',
        metavar='FILE'
    )
    io_group.add_argument(
        '--url',
        nargs='?',
        const='',
        type=str,
        help='Encrypt: output full URL (FILE=save, empty=screen). Decrypt: input from URL file or prompt',
        metavar='FILE'
    )
    io_group.add_argument(
        '--base64',
        nargs='?',
        const='',
        type=str,
        help='Encrypt: output base64 only (FILE=save, empty=screen). Decrypt: input from base64 file or prompt',
        metavar='FILE'
    )
    io_group.add_argument(
        '--clipboard',
        action='store_true',
        help='Encrypt: copy result to clipboard. Decrypt: read QR from clipboard'
    )

    # ========== Other Options ==========
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress security warnings (use with caution!)'
    )

    # ========== Encoding ==========
    parser.add_argument(
        '--encoding',
        type=str,
        default='utf-8',
        help='Text encoding for file input/output (default: utf-8)',
        metavar='ENC'
    )

    # ========== QR Code Parameters ==========
    qr_group = parser.add_argument_group('QR Code Parameters')
    qr_group.add_argument(
        '-b', '--box-size',
        type=int,
        default=50,
        help='QR box size in pixels (default: 50)',
        metavar='N'
    )
    qr_group.add_argument(
        '-r', '--border',
        type=int,
        default=4,
        help='QR border size in boxes (default: 4)',
        metavar='N'
    )
    qr_group.add_argument(
        '--error-correction',
        type=str,
        choices=['L', 'M', 'Q', 'H', 'l', 'm', 'q', 'h'],
        default='H',
        help='QR error correction: L(7%%), M(15%%), Q(25%%), H(30%%) (default: H)',
        metavar='LEVEL'
    )
    qr_group.add_argument(
        '--fill',
        type=str,
        default='black',
        help='QR fill color (default: black)',
        metavar='COLOR'
    )
    qr_group.add_argument(
        '--back',
        type=str,
        default='white',
        help='QR background color (default: white)',
        metavar='COLOR'
    )

    return parser


# ============================================================================
# Main Entry Point
# ============================================================================
def main():
    parser = create_parser()

    # No arguments: show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    # Validate mode selection
    if not any([args.encrypt, args.decrypt, args.encode_qr, args.decode_qr]):
        parser.error("Must specify a mode: -e/--encrypt, -d/--decrypt, --encode-qr, or --decode-qr")

    try:
        if args.encrypt:
            cmd_encrypt(args)
        elif args.decrypt:
            cmd_decrypt(args)
        elif args.encode_qr is not None:  # Changed from boolean to optional argument
            cmd_encode_qr(args)
        elif args.decode_qr is not None:  # Changed from boolean to optional argument
            cmd_decode_qr(args)

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
