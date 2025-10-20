# Project Summary: MX11 Thermal Printer Reverse Engineering

## Objective
To create a fully functional and user-friendly Python toolset for the MX11 thermal printer.

## Recent Major Changes (2025)

### October 19-20, 2025: Major Breakthrough - Anti-Streaking & Web Interface

**CRITICAL FIX: Eliminated Streaking Issues**
- **Root Cause Identified:** Small chunk sizes (4 rows) with timing gaps between chunks caused visible horizontal streaks
- **Solution Implemented:** Adopted Cat-Printer library's proven approach:
  - Single-line chunking (48 bytes per row instead of multi-row chunks)
  - Speed optimization (speed=8, lower = faster)
  - Maximum concentration (0xffff) for darker prints
  - Removed artificial delays that caused printer shutdowns
- **Result:** Dramatically improved print quality with minimal streaking

**NEW: Web Interface (Long-awaited Feature!)**
- Created complete web-based control interface at `http://localhost:8080`
- **Features:**
  - Live image preview with all binarization algorithms
  - Real-time preview updates when changing dithering methods
  - Text printing with configurable font sizes
  - Printer status monitoring and paper control
  - All CLI functionality accessible through clean web UI
- **Files Added:** `web_interface.html`, `web_server.py`, `start_web_interface.bat`

**CLI Binarization Fix**
- **Bug Fixed:** CLI was not properly using the `-b` binarization parameter
- **Solution:** Updated `load_and_prepare_image()` to use `image_convert.preprocess_image()`
- **Result:** All dithering algorithms now work correctly from command line

**Cat-Printer Library Analysis**
- Analyzed successful open-source Cat-Printer implementation
- Adopted their proven printing strategies:
  - Single-line data transmission
  - Optimal speed/concentration settings
  - Consistent timing without artificial delays

- **Advanced Text Printing:**
  - Added support for system fonts (Windows) and configurable font size via CLI/config.
  - Text is now word-wrapped to fit the printer width, preventing cutoff with large fonts.
- **Configuration Improvements:**
  - `config.json` now includes font, fontsize, printer width, and per-dithering-method defaults (threshold, contrast, brightness, etc.).
  - **Default dithering method is now Atkinson.**
- **Image Processing Refactor:**
  - Created `image_convert.py` for all image and text-to-image conversion.
  - Added many dithering algorithms: Floyd-Steinberg, None, Manual, Bayer/Ordered, Atkinson, Burkes, Stucki, Jarvis-Judice-Ninke, Sierra, Random.
  - All image conversion options (dither, threshold, contrast, brightness, etc.) are now configurable and can be tested easily.
- **Code Quality:**
  - All debug output is now controlled by log level (no more print spam).
  - CLI and config-driven workflow for all major options.

## Project Roadmap
1.  **Configuration & CLI:**
    *   Full-Featured CLI & Config File. **(Done)**
2.  **Printing Features:**
    *   Text File Printing. **(Done)**
    *   Advanced Text Printing: Configurable font types and sizes, word wrapping. **(Done)**
    *   Label Calibration. **(Done)**
3.  **Image Processing:**
    *   Refactor Image Processing: Moved to `image_convert.py`. **(Done)**
    *   Advanced Image Conversion: Multiple dithering algorithms, config-driven. **(Done)**
    *   Image Preview GUI: Create a GUI to preview and compare different image settings. **(Done - Web Interface)**
4.  **System Integration:**
    *   **Web Interface: Complete web-based control with live preview.** **(Done)**
    *   Printer Service Emulation: Research options for Windows 11, WSL (with Bluetooth limitations), and Linux (Raspberry Pi) as a network printer. **(Planned)**
    *   Add user prompt: If unable to connect, prompt user to power on the printer. **(Planned)**
5.  **Code Quality:**
    *   Remove Debugging: All debug output now uses logging. **(Done)**
    *   **Anti-Streaking Optimization: Adopted Cat-Printer proven methods.** **(Done)**

## Outstanding Issues
- **Minor Streaking:** Very small streak lines still visible, difference between raw vs on-the-fly conversion
- **Raw vs Processed:** Slight differences between pre-converted images and live processing
- **Battery Status:** Status monitoring doesn't return battery percentage - need to investigate why
- **Missing Commands:** Previous analysis may have missed MX11-specific advanced features

## Next Priority (Oct 20, 2025)
- **🔥 CRITICAL:** Independent analysis of decompiled Fun Print app (`com.fun.mxw.apk`)
- **Investigate:** Why battery % is not returned in status responses
- **Discover:** Advanced/hidden commands beyond basic V5G protocol
- **Find:** MX11-specific optimizations and features not yet implemented

----

**Note:** The MX11 only supports 1bpp (black & white) printing. 4bpp/grayscale is not supported by this model.
