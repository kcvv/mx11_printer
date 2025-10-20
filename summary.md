# MX11 Printer Reverse Engineering Summary

## Objective
To understand the communication protocol of various thermal printers from the "Fun Print" Android application, with the goal of adding support for a new `MX11` model to our Python library.

---

## 1. Key Findings from `app-service.js`

The application uses an internal mapping system to group printers with similar features. Our target printers (`MX01`, `MX10`, etc.) are all part of a family internally identified as **`V5G`**.

### `V5G` Family Characteristics:

*   **Print Speed:** The app explicitly sets the print speed to `60` for these models using the command `5178F1...`. Other models use different speeds.
*   **Print Concentration (Density):** The app can set the print density using the command `5178F2...`. This is a key part of the thermal protection feature.
*   **Thermal Head Protection:** For `V5G` models, the app includes logic to prevent the print head from overheating. It does this by lowering the print concentration on successive rapid prints.
*   **Label Printing & Calibration:** There is dedicated logic for label printing, including a specific **calibration command** (`5178F0...`) to align the paper feed. This is a strong indicator that `MX` series printers support label mode.
*   **Status Queries:** The app actively queries the printer's status before printing using the command `5178A3...` to check for "paper out," "overheating," and "low battery" conditions.

---

## 2. Strategy for Supporting the `MX11`

Our primary strategy is to **treat the `MX11` as a `V5G` family printer**.

1.  **Confirm its Identity:** Use the `V5G`-specific status query command (`5178A3...`). A valid response strongly indicates it belongs to this family.
2.  **Test Feature by Feature:** Implement and test the commands for print speed, concentration, and label calibration to discover the full capabilities of the `MX11`.

---

## 3. Changes Made to `printer.py`

Based on the findings, we have made the following improvements to the Python library:

*   **Added `PrinterProfile`:** Created a `V5G_PROFILE` to store model-specific settings (`speed=60`, `concentration=110`, etc.), making the code cleaner and more extensible.
*   **Implemented `crc8()`:** Added a function to calculate the CRC-8 checksum required by some commands.
*   **Added Status Checking (`get_status`)**:
    *   Sends the `V5G` status query command (`5178A3...`).
    *   Parses the 10-byte response to determine the printer's state (OK, No Paper, Overheating, Low Battery).
    *   This is our primary method for **verifying the `MX11` is a `V5G` device**.
*   **Added Advanced Commands:**
    *   `set_speed(speed)`: To configure the print speed.
    *   `set_concentration(concentration)`: To set the print density, including the calculated CRC.
*   **Improved `print_image()` Logic:** The printing sequence is now more robust:
    1.  Connect to the printer.
    2.  Call `get_status()` to ensure the printer is ready.
    3.  Call `set_speed()` to apply the optimal speed from the profile.
    4.  Send the image data.

---

## 4. Next Steps

*   Experiment with different concentration values using `set_concentration()` to see how it affects print quality.
*   Begin reverse-engineering the image-to-hex data format for more precise print control.
*   Research printer service emulation options:
    - Windows 11 native service (challenging, but possible)
    - Linux service on WSL (note: WSL may have Bluetooth limitations)
    - Linux (e.g., Raspberry Pi) as a network printer server (recommended for always-on setup)
*   Add user guidance: If unable to connect, prompt user to power on the printer (since it auto-sleeps).

---

**Note:** The MX11 only supports 1bpp (black & white) printing. 4bpp/grayscale is not supported by this model.