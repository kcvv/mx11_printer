# c:\Users\Venky\Downloads\Cat-Printer-main\mx11_printer\test_features.py

import asyncio
from mx11 import Printer
import os

# --- IMPORTANT ---
# 1. Replace with your printer's MAC address
PRINTER_MAC = "CA:06:26:70:8B:06" 

# 2. Create a small test image (e.g., 384x100 pixels) and save it as `test.png`
#    in the same folder as this script.
TEST_IMAGE_PATH = "test.png"

async def main():
    if PRINTER_MAC == "XX:XX:XX:XX:XX:XX":
        print("Please update the PRINTER_MAC address in the script.")
        return
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"Test image '{TEST_IMAGE_PATH}' not found. Please create it.")
        return

    printer = Printer(PRINTER_MAC)
    try:
        await printer.connect()

        print("\n--- 1. Testing Status Query ---")
        is_v5g = await printer.get_status()
        if is_v5g:
            print("\nConclusion: The printer responded correctly. It is a V5G-family device!")
        else:
            print("\nConclusion: The printer did not respond as expected. It may not be a V5G-family device.")

        print("\n--- 2. Testing Serial Number Query ---")
        await printer.get_serial_number()

        print("\n--- 3. Testing Label Calibration ---")
        await printer.calibrate()
        await asyncio.sleep(3) # Give printer time to react
        
        print("\n--- 4. Testing Print Concentration ---")
        print("Setting concentration to HIGH (150) and printing...")
        await printer.set_concentration(150)
        await printer.print_image(TEST_IMAGE_PATH)
        
        await asyncio.sleep(5) # Wait for the first print to finish
        
        print("\nSetting concentration to LOW (80) and printing...")
        await printer.set_concentration(80)
        await printer.print_image(TEST_IMAGE_PATH)
        print("\nCompare the two prints. The first should be darker than the second.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        await printer.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
