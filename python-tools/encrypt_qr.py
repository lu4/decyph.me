#!/usr/bin/env python3
import os, base64, getpass, secrets, unicodedata as u, urllib.parse as up
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

def main():
    mode = input("[E]ncrypt / [D]ecrypt? ").strip().lower()[:1]
    if mode == "e":
        text = input("Enter text to encrypt: ")
        pw1 = getpass.getpass("Enter password: ")
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
        pw = getpass.getpass("Enter password: ")
        try:
            print("\nDecrypted:\n" + decrypt(data, pw))
        except Exception:
            print("Decryption failed (wrong password or data tampered).")
    else:
        print("Choose E or D.")

if __name__ == "__main__":
    main()


# https://decyph.me/#ARIIAY15eMKcKpCWoCRMl73xcCrVAuSnWyBestm0g5Ldh4Zl7qpSixL0MHhdpTTzfd5ae9AihbkJZ2Wi1XHiu2EW2G3+EmX6anioWAk6O5L3xw==