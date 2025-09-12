#!/usr/bin/env python3

import os
import sys
import qrcode

def generate_qr_console(data: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii()

def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "decrypt_qr_minimal.py"
    
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' does not exist.")
        sys.exit(1)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filename, 'rb') as f:
                import base64
                content = base64.urlsafe_b64encode(f.read()).decode()
                print("Binary file detected, encoded as base64")
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    print(f"Encoding file: {filename}")
    print(f"Content length: {len(content)} characters")
    
    print("\nQR Code:")
    generate_qr_console(content)

if __name__ == "__main__":
    main()
