#!/usr/bin/env python3
"""
QR Code Decoder - Extract text from QR code images

Usage:
    python decode_qr.py <image_path>
    python decode_qr.py image.png
    python decode_qr.py --clipboard  # Decode from clipboard image (macOS/Linux with xclip)
"""

import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
    from pyzbar.pyzbar import decode as pyzbar_decode
except ImportError as e:
    print(f"Error: Missing required library: {e.name}")
    print("\nPlease install required dependencies:")
    print("  pip install pillow pyzbar")
    print("\nNote: pyzbar also requires the zbar library:")
    print("  - macOS: brew install zbar")
    print("  - Ubuntu/Debian: sudo apt-get install libzbar0")
    print("  - Fedora: sudo dnf install zbar")
    sys.exit(1)


def decode_qr_from_file(image_path: str) -> str:
    """
    Decode QR code from an image file.

    Args:
        image_path: Path to the image file

    Returns:
        Decoded text from QR code

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If no QR code found in image
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Open and decode the image
    try:
        img = Image.open(path)
    except Exception as e:
        raise ValueError(f"Failed to open image: {e}")

    # Decode QR codes
    decoded_objects = pyzbar_decode(img)

    if not decoded_objects:
        raise ValueError("No QR code found in the image")

    if len(decoded_objects) > 1:
        print(f"Warning: Found {len(decoded_objects)} QR codes, using the first one", file=sys.stderr)

    # Extract the data from the first QR code
    qr_data = decoded_objects[0].data.decode('utf-8')
    return qr_data


def decode_qr_from_clipboard():
    """
    Decode QR code from clipboard image (platform-specific).
    """
    try:
        # Try to get image from clipboard
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()

        if img is None:
            raise ValueError("No image found in clipboard")

        if not isinstance(img, Image.Image):
            raise ValueError("Clipboard content is not an image")

        # Decode QR codes
        decoded_objects = pyzbar_decode(img)

        if not decoded_objects:
            raise ValueError("No QR code found in the clipboard image")

        if len(decoded_objects) > 1:
            print(f"Warning: Found {len(decoded_objects)} QR codes, using the first one", file=sys.stderr)

        return decoded_objects[0].data.decode('utf-8')

    except ImportError:
        raise ValueError("Clipboard functionality not available on this platform")


def main():
    parser = argparse.ArgumentParser(
        description="Decode text from QR code images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python decode_qr.py qrcode.png
  python decode_qr.py ~/Downloads/encrypted.png
  python decode_qr.py --clipboard
  python decode_qr.py ledger-new-root-password.png
        """
    )

    parser.add_argument(
        'image_path',
        nargs='?',
        help='Path to QR code image file'
    )

    parser.add_argument(
        '--clipboard', '-c',
        action='store_true',
        help='Decode QR code from clipboard image'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only output the decoded text (no labels or errors)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.clipboard and args.image_path:
        parser.error("Cannot specify both image_path and --clipboard")

    if not args.clipboard and not args.image_path:
        parser.error("Must specify either image_path or --clipboard")

    try:
        # Decode from clipboard or file
        if args.clipboard:
            qr_text = decode_qr_from_clipboard()
            if not args.quiet:
                print("Decoded from clipboard:")
        else:
            qr_text = decode_qr_from_file(args.image_path)
            if not args.quiet:
                print(f"Decoded from {args.image_path}:")

        # Output the decoded text
        print(qr_text)

        # Exit successfully
        return 0

    except (FileNotFoundError, ValueError) as e:
        if args.quiet:
            sys.exit(1)
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        if args.quiet:
            sys.exit(1)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
