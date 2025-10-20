# MX11 Thermal Printer Library

Python library for controlling MX11 and V5G-family thermal printers via Bluetooth Low Energy (BLE).

## Features

- ✅ **Print images** with automatic processing and dithering
- ✅ **Print text** with custom fonts and sizes  
- ✅ **Optimal settings** based on Fun Print app analysis
- ✅ **Easy-to-use CLI** with intuitive speed/darkness controls
- ✅ **Cross-platform** BLE support via bleak
- ✅ **Multiple image formats** supported (PNG, JPG, etc.)

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
# Print an image with optimal settings
python printer.py --image photo.jpg --speed 2 --concentration 125

# Print text file
python printer.py --textfile document.txt --speed 2 --concentration 125

# Feed paper
python printer.py --feed 5
```

### Easy Settings Helper

Use the settings helper for human-readable options:

```bash
# Get optimal settings
python better_settings.py medium dark
# Output: --speed 2 --concentration 137

# Use with printer
python printer.py --image photo.jpg --speed 2 --concentration 137
```

## Settings Guide

### Speed Options
- `fast` → `--speed 1`
- `medium` → `--speed 2` (recommended)
- `slow` → `--speed 3`

### Darkness Options
- `light` → `--concentration 112` (25%)
- `medium` → `--concentration 125` (50%, recommended)
- `dark` → `--concentration 137` (75%)
- `max` → `--concentration 150` (100%)
- Custom: Any 0-100 percentage

## Configuration

Edit `config.json` to set your printer's MAC address:

```json
{
  "mac_address": "CA:06:26:70:8B:06",
  "defaults": {
    "speed": 2,
    "concentration": 125,
    "feed_lines": 3
  }
}
```

## Supported Printers

- MX11 series thermal printers
- V5G-family printers
- Compatible BLE thermal printers using similar protocols

## Files Overview

### Core Files
- `mx11.py` - Main printer library with MX11 protocol implementation
- `printer.py` - Command-line interface for printer control
- `better_settings.py` - Human-readable settings helper
- `config.json` - Configuration file for defaults

### Utilities
- `image_convert.py` - Image processing utilities
- `web_server.py` - Web interface for printer control
- `web_interface.html` - Web UI

### Tests
- `tests/` - Test scripts for development

## Protocol Details

This library implements the MX11 thermal printer protocol based on analysis of the Fun Print Android application. Key findings:

- **Optimal density range**: 100-150 (mapped from 0-100% user input)
- **Speed settings**: 1-3 (fast to slow)
- **Print width**: 384 pixels
- **Command structure**: `51 78` prefix with specific payloads

## Development

The library was developed through reverse engineering of the Fun Print app, which acts as an ESC/POS to MX11 protocol translator. This analysis revealed the optimal settings and command structures used in this implementation.

## License

GPL-3.0 License - see LICENSE file for details.

## Contributing

Contributions welcome! Please test with your specific printer model and report compatibility.

## Troubleshooting

### Common Issues

1. **No response from printer**: Some MX11 printers are write-only and don't send status responses
2. **Connection failed**: Ensure printer is in pairing mode and MAC address is correct
3. **Poor print quality**: Adjust darkness/concentration settings using the helper

### Getting Help

1. Check your printer's MAC address: Use your system's Bluetooth settings
2. Test basic connection: `python printer.py --feed 1`
3. Try different settings: Use `better_settings.py` to find optimal values

## Acknowledgments

- Fun Print Android app analysis provided crucial protocol insights
- bleak library for cross-platform BLE support
- PIL/Pillow for image processing
