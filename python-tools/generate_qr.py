#!/usr/bin/env python3
"""
QR Code Generator - Comprehensive command-line tool for generating QR codes as PNG images.

Supports input from stdin, files, or command-line arguments with full control over
all QR code generation parameters including size, error correction, colors, and more.
"""

import sys
import argparse
import qrcode
from pathlib import Path


def create_qr_code(
    data: str,
    output: str,
    version: int = None,
    error_correction: str = 'H',
    box_size: int = 50,
    border: int = 4,
    fill_color: str = 'black',
    back_color: str = 'white',
    optimize: int = 20,
) -> None:
    """
    Generate a QR code image and save it as PNG.

    Args:
        data: Content to encode in the QR code
        output: Output PNG file path
        version: QR code version (1-40, None for auto)
        error_correction: Error correction level (L, M, Q, H)
        box_size: Size of each box in pixels
        border: Border size in boxes
        fill_color: Foreground/fill color
        back_color: Background color
        optimize: Data chunks optimization threshold
    """
    # Map error correction string to constant
    error_correction_map = {
        'L': qrcode.constants.ERROR_CORRECT_L,  # ~7% correction
        'M': qrcode.constants.ERROR_CORRECT_M,  # ~15% correction
        'Q': qrcode.constants.ERROR_CORRECT_Q,  # ~25% correction
        'H': qrcode.constants.ERROR_CORRECT_H,  # ~30% correction
    }

    ec_level = error_correction_map.get(error_correction.upper())
    if ec_level is None:
        raise ValueError(f"Invalid error correction level: {error_correction}")

    # Create QR code instance
    qr = qrcode.QRCode(
        version=version,
        error_correction=ec_level,
        box_size=box_size,
        border=border,
    )

    # Add data and generate QR code
    qr.add_data(data, optimize=optimize)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    # Save to file
    img.save(output)

    # Print info
    actual_version = qr.version
    data_length = len(data)
    print(f"QR code generated successfully:", file=sys.stderr)
    print(f"  Output: {output}", file=sys.stderr)
    print(f"  Version: {actual_version}", file=sys.stderr)
    print(f"  Error correction: {error_correction.upper()}", file=sys.stderr)
    print(f"  Data length: {data_length} characters", file=sys.stderr)
    print(f"  Image size: {img.size[0]}x{img.size[1]} pixels", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='Generate QR codes as PNG images from text input',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from stdin
  echo "Hello, World!" | %(prog)s -o qr.png

  # Generate from file
  %(prog)s -f message.txt -o qr.png

  # Generate from command-line text
  %(prog)s -t "https://example.com" -o qr.png

  # Customize QR code parameters
  %(prog)s -t "My data" -o qr.png -v 5 -e H -b 20 -r 2

  # Custom colors
  %(prog)s -t "Colorful QR" -o qr.png --fill blue --back yellow

  # High resolution for printing
  %(prog)s -f file.txt -o qr.png -b 50 -r 10

Error Correction Levels:
  L - Low      (~7%% correction)  - Maximum data capacity
  M - Medium   (~15%% correction) - Balanced (default)
  Q - Quartile (~25%% correction) - Good for damaged codes
  H - High     (~30%% correction) - Best reliability

QR Code Versions:
  1-40: Fixed version (larger number = more data capacity)
  auto: Automatically choose minimum version needed (default)
        """
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        '-f', '--file',
        type=str,
        help='Read input from file',
        metavar='FILE'
    )
    input_group.add_argument(
        '-t', '--text',
        type=str,
        help='Input text directly from command line',
        metavar='TEXT'
    )

    # Output options
    parser.add_argument(
        '-o', '--output',
        type=str,
        required=True,
        help='Output PNG file path',
        metavar='FILE'
    )

    # QR code parameters
    parser.add_argument(
        '-v', '--version',
        type=int,
        choices=range(1, 41),
        default=None,
        help='QR code version (1-40), auto if not specified',
        metavar='N'
    )

    parser.add_argument(
        '-e', '--error-correction',
        type=str,
        choices=['L', 'M', 'Q', 'H', 'l', 'm', 'q', 'h'],
        default='H',
        help='Error correction level: L (low), M (medium), Q (quartile), H (high). Default: H',
        metavar='LEVEL'
    )

    parser.add_argument(
        '-b', '--box-size',
        type=int,
        default=50,
        help='Size of each box in pixels. Default: 50',
        metavar='N'
    )

    parser.add_argument(
        '-r', '--border',
        type=int,
        default=4,
        help='Border size in boxes (min 4 recommended). Default: 4',
        metavar='N'
    )

    parser.add_argument(
        '--fill',
        type=str,
        default='black',
        help='Fill color (foreground). Default: black',
        metavar='COLOR'
    )

    parser.add_argument(
        '--back',
        type=str,
        default='white',
        help='Background color. Default: white',
        metavar='COLOR'
    )

    parser.add_argument(
        '--optimize',
        type=int,
        default=20,
        help='Data optimization threshold. Default: 20',
        metavar='N'
    )

    parser.add_argument(
        '--encoding',
        type=str,
        default='utf-8',
        help='Text encoding for file input. Default: utf-8',
        metavar='ENCODING'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress informational output'
    )

    args = parser.parse_args()

    # Redirect stderr to null if quiet mode
    if args.quiet:
        sys.stderr = open('/dev/null', 'w')

    # Get input data
    try:
        if args.text:
            # Direct text input
            data = args.text
        elif args.file:
            # Read from file
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File not found: {args.file}", file=sys.stderr)
                sys.exit(1)

            try:
                data = file_path.read_text(encoding=args.encoding)
            except UnicodeDecodeError as e:
                print(f"Error: Cannot decode file with {args.encoding} encoding: {e}", file=sys.stderr)
                print("Try specifying a different encoding with --encoding", file=sys.stderr)
                sys.exit(1)
        else:
            # Read from stdin
            if sys.stdin.isatty():
                print("Reading from stdin (Ctrl+D to finish):", file=sys.stderr)
            data = sys.stdin.read()

        # Check if data is empty
        if not data:
            print("Error: No input data provided", file=sys.stderr)
            sys.exit(1)

        # Generate QR code
        create_qr_code(
            data=data,
            output=args.output,
            version=args.version,
            error_correction=args.error_correction,
            box_size=args.box_size,
            border=args.border,
            fill_color=args.fill,
            back_color=args.back,
            optimize=args.optimize,
        )

    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
