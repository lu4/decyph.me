#!/usr/bin/env python3
import os, base64, getpass, secrets, unicodedata as u, urllib.parse as up
import sys
import argparse
from pathlib import Path
import qrcode
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- Tunables (embedded in header) ---
VER = 1                 # format version (kept for compatibility)
LOGN, R, P = 18, 8, 1   # scrypt: N=2^18 (~256 MiB), r=8, p=1
KEYLEN = 32             # AES-256-GCM
SALTLEN = 16
NONCELEN = 12
MIN_PW_LEN = 14
BASE_URL = "https://decyph.me/#"

def _hdr_bytes(): return bytes([VER, LOGN, R, P])

def _parse_hdr(h):
    if len(h) != 4 or h[0] != VER: raise ValueError("bad header/version")
    return (1 << h[1]), h[2], h[3]  # N, r, p

def _norm_pwd(pw: str) -> bytes:
    return u.normalize("NFC", pw).encode("utf-8")

def _kdf_scrypt(pw_bytes: bytes, salt: bytes, N: int, r: int, p: int, ln: int) -> bytes:
    return Scrypt(salt=salt, length=ln, n=N, r=r, p=p).derive(pw_bytes)

def _strong_pw(p: str) -> bool:
    if len(p) < MIN_PW_LEN: return False
    classes = sum(any(getattr(c, "isascii")() and test(c) for c in p) for test in (str.islower, str.isupper, str.isdigit))
    specials = any(not c.isalnum() for c in p)
    return classes + (1 if specials else 0) >= 3  # need 3 of: lower/upper/digit/special

def encrypt(plaintext: str, password: str) -> str:
    salt, nonce = os.urandom(SALTLEN), os.urandom(NONCELEN)
    key = _kdf_scrypt(_norm_pwd(password), salt, 1 << LOGN, R, P, KEYLEN)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), _hdr_bytes() + salt + nonce)
    blob = _hdr_bytes() + salt + nonce + ct
    return base64.urlsafe_b64encode(blob).decode("ascii")

def _extract_b64(s: str) -> str:
    # Accept either raw Base64 or a URL like https://decyph.me/qr#<base64>
    if s.startswith("http://") or s.startswith("https://"):
        s = up.unquote(s)
        i = s.find("#")
        if i != -1:
            return s[i+1:]  # everything after '#'
    return s

def decrypt(b64_or_url: str, password: str) -> str:
    raw_b64 = _extract_b64(b64_or_url)
    raw = base64.urlsafe_b64decode(raw_b64)
    if len(raw) < 4 + SALTLEN + NONCELEN: raise ValueError("truncated")
    hdr, rest = raw[:4], raw[4:]
    N, r, p = _parse_hdr(hdr)
    salt = rest[:SALTLEN]; nonce = rest[SALTLEN:SALTLEN+NONCELEN]; ct = rest[SALTLEN+NONCELEN:]
    key = _kdf_scrypt(_norm_pwd(password), salt, N, r, p, KEYLEN)
    pt = AESGCM(key).decrypt(nonce, ct, hdr + salt + nonce)
    return pt.decode("utf-8")

def generate_qr_console(data: str):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=1, border=1)
    qr.add_data(data); qr.make(fit=True); qr.print_ascii()

def generate_qr_png(
    data: str,
    output: str,
    box_size: int = 50,
    border: int = 4,
    error_correction: str = 'H',
    fill_color: str = 'black',
    back_color: str = 'white',
) -> None:
    """Generate a QR code and save as PNG file."""
    error_correction_map = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H,
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

    print(f"QR code saved to: {output}", file=sys.stderr)
    print(f"  Version: {qr.version}", file=sys.stderr)
    print(f"  Image size: {img.size[0]}x{img.size[1]} pixels", file=sys.stderr)

def interactive_mode():
    """Original interactive mode."""
    mode = input("[E]ncrypt / [D]ecrypt? ").strip().lower()[:1]
    if mode == "e":
        text = input("Enter text to encrypt: ")
        pw1 = getpass.getpass("\nEnter password: ")
        pw2 = getpass.getpass("Confirm password: ")
        if not secrets.compare_digest(pw1, pw2):
            print("Passwords do not match."); return
        if not _strong_pw(pw1):
            print(f"Password too weak (min {MIN_PW_LEN} chars, mix of classes)."); return
        b64 = encrypt(text, pw1)
        link = BASE_URL + b64
        print("\nEncrypted data (Base64):\n" + b64)
        print("\nLink:\n" + link)
        print("\nQR Code (link):"); generate_qr_console(link)
    elif mode == "d":
        data = input("Enter Base64 or URL: ")
        pw = getpass.getpass("\nEnter password: ")
        try:
            print("\nDecrypted:\n" + decrypt(data, pw))
        except Exception:
            print("Decryption failed (wrong password or data tampered).")
    else:
        print("Choose E or D.")

def main():
    parser = argparse.ArgumentParser(
        description='Encrypt/decrypt text with AES-256-GCM and generate QR codes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (no arguments)
  %(prog)s

  # Encrypt text and save QR code
  %(prog)s -e -t "Secret message" -p MyPassword123! -o qr.png

  # Encrypt from file and save QR code
  %(prog)s -e -f message.txt -o encrypted_qr.png

  # Encrypt with custom QR code parameters
  %(prog)s -e -t "Data" -o qr.png -b 30 --error-correction H

  # Decrypt encrypted data
  %(prog)s -d -t "ARIIAY15eM..." -p MyPassword123!

  # Decrypt from URL
  %(prog)s -d -t "https://decyph.me/#ARIIAY15eM..."

Note: If password is not provided with -p, you will be prompted securely.
        """
    )

    # Mode selection
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

    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        '-t', '--text',
        type=str,
        help='Input text directly',
        metavar='TEXT'
    )
    input_group.add_argument(
        '-f', '--file',
        type=str,
        help='Read input from file',
        metavar='FILE'
    )

    # Password
    parser.add_argument(
        '-p', '--password',
        type=str,
        help='Password (will prompt securely if not provided)',
        metavar='PASSWORD'
    )

    # QR code output (for encrypt mode)
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output PNG file for QR code (encrypt mode only)',
        metavar='FILE'
    )

    # QR code parameters
    parser.add_argument(
        '-b', '--box-size',
        type=int,
        default=50,
        help='QR code box size in pixels. Default: 50',
        metavar='N'
    )

    parser.add_argument(
        '-r', '--border',
        type=int,
        default=4,
        help='QR code border size in boxes. Default: 4',
        metavar='N'
    )

    parser.add_argument(
        '--error-correction',
        type=str,
        choices=['L', 'M', 'Q', 'H', 'l', 'm', 'q', 'h'],
        default='H',
        help='QR code error correction level. Default: H',
        metavar='LEVEL'
    )

    parser.add_argument(
        '--fill',
        type=str,
        default='black',
        help='QR code fill color. Default: black',
        metavar='COLOR'
    )

    parser.add_argument(
        '--back',
        type=str,
        default='white',
        help='QR code background color. Default: white',
        metavar='COLOR'
    )

    parser.add_argument(
        '--no-link',
        action='store_true',
        help='Generate QR code from base64 data only (no URL prefix)'
    )

    parser.add_argument(
        '--encoding',
        type=str,
        default='utf-8',
        help='Text encoding for file input. Default: utf-8',
        metavar='ENCODING'
    )

    # If no arguments provided, run interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
        return

    args = parser.parse_args()

    # Check if mode is selected
    if not args.encrypt and not args.decrypt:
        parser.error("Please specify either -e/--encrypt or -d/--decrypt mode")

    try:
        if args.encrypt:
            # Get input text
            if args.text:
                plaintext = args.text
            elif args.file:
                file_path = Path(args.file)
                if not file_path.exists():
                    print(f"Error: File not found: {args.file}", file=sys.stderr)
                    sys.exit(1)
                try:
                    plaintext = file_path.read_text(encoding=args.encoding)
                except UnicodeDecodeError as e:
                    print(f"Error: Cannot decode file with {args.encoding} encoding: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                # Read from stdin
                if sys.stdin.isatty():
                    print("Reading from stdin (Ctrl+D to finish):", file=sys.stderr)
                plaintext = sys.stdin.read()

            if not plaintext:
                print("Error: No input data provided", file=sys.stderr)
                sys.exit(1)

            # Get password
            if args.password:
                pw1 = args.password
                pw2 = pw1
            else:
                pw1 = getpass.getpass("\nEnter password: ")
                pw2 = getpass.getpass("Confirm password: ")

            if not secrets.compare_digest(pw1, pw2):
                print("Error: Passwords do not match", file=sys.stderr)
                sys.exit(1)

            if not _strong_pw(pw1):
                print(f"Error: Password too weak (min {MIN_PW_LEN} chars, 3+ character classes)", file=sys.stderr)
                sys.exit(1)

            # Encrypt
            b64 = encrypt(plaintext, pw1)
            link = BASE_URL + b64

            # Output encrypted data
            print("\nEncrypted data (Base64):")
            print(b64)
            print("\nLink:")
            print(link)

            # Generate QR code
            if args.output:
                qr_data = b64 if args.no_link else link
                generate_qr_png(
                    data=qr_data,
                    output=args.output,
                    box_size=args.box_size,
                    border=args.border,
                    error_correction=args.error_correction,
                    fill_color=args.fill,
                    back_color=args.back,
                )

                # Save link to file with .link suffix
                link_file = args.output + '.link'
                Path(link_file).write_text(qr_data + '\n')
                print(f"Link saved to: {link_file}", file=sys.stderr)
            else:
                print("\nQR Code (link):")
                generate_qr_console(link)

        elif args.decrypt:
            # Get encrypted data
            if args.text:
                encrypted_data = args.text
            elif args.file:
                file_path = Path(args.file)
                if not file_path.exists():
                    print(f"Error: File not found: {args.file}", file=sys.stderr)
                    sys.exit(1)
                encrypted_data = file_path.read_text(encoding=args.encoding).strip()
            else:
                # Read from stdin
                if sys.stdin.isatty():
                    print("Reading encrypted data from stdin (Ctrl+D to finish):", file=sys.stderr)
                encrypted_data = sys.stdin.read().strip()

            if not encrypted_data:
                print("Error: No encrypted data provided", file=sys.stderr)
                sys.exit(1)

            # Get password
            if args.password:
                pw = args.password
            else:
                pw = getpass.getpass("\nEnter password: ")

            # Decrypt
            try:
                decrypted = decrypt(encrypted_data, pw)
                print("\nDecrypted:")
                print(decrypted)
            except Exception as e:
                print(f"Error: Decryption failed (wrong password or data tampered)", file=sys.stderr)
                sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()