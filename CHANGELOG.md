# Changelog

## [2.0.0] - 2025-01-20

### Added
- **Fun Print Analysis Integration**: Reverse-engineered optimal settings from Fun Print Android app
- **Improved Settings System**: Human-readable speed (fast/medium/slow) and darkness (0-100%) options
- **Settings Helper**: `better_settings.py` for easy parameter conversion
- **Optimal Defaults**: Based on Fun Print analysis (speed=2, concentration=125)
- **Enhanced Documentation**: Comprehensive README with troubleshooting guide

### Changed
- **Default Speed**: Changed from 60 to 2 (medium) based on Fun Print analysis
- **Default Concentration**: Changed from 110 to 125 (medium darkness) for better print quality
- **Concentration Range**: Now maps 0-100% to MX11 range 100-150 (Fun Print optimal values)

### Fixed
- **Battery Command**: Corrected missing byte in battery status command
- **Command Structure**: Verified against Fun Print protocol implementation
- **Print Quality**: Improved defaults result in better image and text output

### Technical Details
- Analyzed Fun Print APK to understand ESC/POS to MX11 conversion
- Discovered optimal density settings: text_model and image_model both use 100-150 range
- Confirmed MX11 protocol uses `51 78` command prefix with specific payload structures
- Identified that some MX11 printers are write-only (accept commands but don't send responses)

## [1.0.0] - Previous Version

### Features
- Basic MX11 printer support
- Image and text printing
- BLE connectivity via bleak
- Web interface
- Command-line interface

### Known Issues
- Suboptimal default settings
- Limited documentation
- Inconsistent print quality
