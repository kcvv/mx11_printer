# MX11 Cat Printer - Consolidated Python Library

A single-file Python library for printing text and images to MX11 thermal printers via Bluetooth Low Energy (BLE).

## Credits

This project is an extension of two excellent open-source projects:
- [NaitLee/Cat-Printer](https://github.com/NaitLee/Cat-Printer) - Comprehensive cat printer library with font support
- [rbaron/catprinter](https://github.com/rbaron/catprinter) - Original reverse-engineered BLE communication protocol

This consolidated version specifically supports the **MX11 version** of the cat printer and combines the best features from both projects into a single, easy-to-use file.

## Features

- **Single file solution** - All functionality in one `printer.py` file
- **Text printing** with configurable fonts (PF2 format)
- **Image printing** (JPG, PNG with automatic resizing and dithering)
- **Multiple input sources** - Direct text, files, or stdin
- **Paper feed control** - Adjustable paper advancement
- **Font management** - List and select from available fonts
- **Test mode** - Generate images without printing

## Installation

```bash
# Clone or download the repository
git clone <your-repo-url>
cd mx11_printer

# Install dependencies
pip install -r requirements.txt
```

### Requirements
- Python 3.7+
- `bleak` - Bluetooth Low Energy communication
- `Pillow` - Image processing

## Usage

### Basic Commands

```bash
# Print text (default font)
python printer.py --text "Hello World!"

# Print text from file
python printer.py --file mytext.txt

# Print text from stdin
echo "Hello from pipe!" | python printer.py --stdin

# Print image
python printer.py --image photo.jpg
```

### Font Options

```bash
# List available fonts
python printer.py --list-fonts

# Use custom font for text
python printer.py --text "Custom font text" --font fonts/Helvetica-18.pf2

# Print file with small font
python printer.py --file document.txt --font fonts/Helvetica-12.pf2
```

### Paper Feed

```bash
# Feed 25 pixels of paper
python printer.py --feed 25

# Print with extra paper feed
python printer.py --text "Hello" --feed 50
```

### Test Mode

```bash
# Test text generation without printing
python printer.py --test --text "Test text"

# Test file processing
python printer.py --test --file myfile.txt --font fonts/Helvetica-18.pf2
```

### Configuration

```bash
# Use custom printer MAC address
python printer.py --text "Hello" --mac "AA:BB:CC:DD:EE:FF"
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--text TEXT` | Print the given text as an image |
| `--file FILE` | Print text from file |
| `--stdin` | Read text from standard input |
| `--image FILE` | Print image file (jpg/png) |
| `--font FONT` | Font file for text rendering (default: fonts/Helvetica-24.pf2) |
| `--mac MAC` | Printer MAC address (default: CA:06:26:70:8B:06) |
| `--feed PIXELS` | Feed paper by specified pixels |
| `--test` | Test mode - generate without printing |
| `--list-fonts` | List available fonts |

## Examples

### Print System Information
```bash
# Windows
systeminfo | python printer.py --stdin --font fonts/Helvetica-12.pf2

# Linux/Mac
uname -a | python printer.py --stdin
```

### Print Code Files
```bash
# Print Python file with small font
python printer.py --file script.py --font fonts/Helvetica-10.pf2
```

### Print with Spacing
```bash
# Print multiple items with spacing
python printer.py --text "Item 1" --feed 30
python printer.py --text "Item 2" --feed 30
```

## Font Files

The printer uses PF2 font files. Included fonts:
- Helvetica (8, 10, 12, 14, 18, 24 pt)
- New Century Schoolbook (8, 10, 12, 14, 18, 24 pt)
- Various decorative fonts

## Troubleshooting

### Printer Not Found
- Ensure printer is powered on
- Check MAC address is correct
- Make sure printer is in pairing mode

### Font Errors
- Use `--list-fonts` to see available fonts
- Ensure font path is correct (no quotes needed)
- Default font: `fonts/Helvetica-24.pf2`

### Test Without Printer
```bash
# Test image generation
python printer.py --test --text "Test text"
```

## Technical Details

- **Print Width**: 384 pixels
- **Communication**: Bluetooth Low Energy (BLE)
- **Image Format**: 1-bit monochrome with Floyd-Steinberg dithering
- **Font Format**: PF2 (GRUB font format)
- **Paper Feed**: Configurable in pixels (typical: 8-50 pixels)

## File Structure

```
mx11_printer/
├── printer.py          # Main consolidated library
├── fonts/              # PF2 font files
│   ├── Helvetica-24.pf2
│   ├── Helvetica-18.pf2
│   └── ...
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This project builds upon the work of the original projects:
- [NaitLee/Cat-Printer](https://github.com/NaitLee/Cat-Printer) - CC0-1.0 License
- [rbaron/catprinter](https://github.com/rbaron/catprinter) - MIT License

## Contributing

Feel free to submit issues and pull requests to improve the MX11 support and add new features.