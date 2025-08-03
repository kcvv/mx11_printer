# Cat Printer Cleanup Plan

## Files that can be REMOVED (not used by basic_printer_test.py):

### catprinter/ directory:
- `ble.py` - Alternative BLE implementation (you use bleak directly)
- `img.py` - Advanced image processing with OpenCV (you use PIL instead)

### printer_lib/ directory:
- `commander.py` - Alternative printer command interface
- `i18n.py` - Internationalization support
- `ipp.py` - CUPS/IPP printer support
- `models.py` - Printer model specifications

### fonts/ directory:
Keep only: `Helvetica-24.pf2` (used in your code)
Remove all other .pf2 files (57 font files can be deleted)

## Files to KEEP (required for functionality):

### Core files:
- `basic_printer_test.py` - Your main application
- `cat.jpg` - Default test image
- `requirements.txt` - Dependencies (needs to be created/updated)

### catprinter/ directory:
- `__init__.py` - Module initialization
- `cmds.py` - Core printer commands

### printer_lib/ directory:
- `__init__.py` - Module initialization  
- `text_print.py` - Text rendering
- `pf2.py` - Font file handling

### fonts/ directory:
- `Helvetica-24.pf2` - Font used by your application

## Required dependencies for requirements.txt:
```
bleak>=0.20.0
Pillow>=9.0.0
```

## Estimated space savings:
- Font files: ~2-3 MB (keeping only 1 out of 58 fonts)
- Unused Python modules: ~50 KB
- Total savings: ~2-3 MB (mostly fonts)