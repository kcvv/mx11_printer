import argparse
def print_usage():
    print("""
Cat Printer Test Utility

Usage:
  python basic_printer_test.py [--text "Hello World!"] [--image cat.jpg]

Options:
  -h, --help         Show this help message and exit
  --text TEXT        Print the given text as an image
  --image FILE       Print the given image file (jpg/png)

If no options are given, both a default text and the default image (cat.jpg) will be printed.
""")
from PIL import Image
def load_and_prepare_image(path):
    # Load image, resize to printer width, dither to 1-bit using Floyd-Steinberg
    img = Image.open(path).convert('L')
    new_height = int(img.height * PRINT_WIDTH / img.width)
    img = img.resize((PRINT_WIDTH, new_height), Image.LANCZOS)
    img = img.convert('1')  # Uses Floyd-Steinberg dithering by default
    # Convert to list of rows of 0/1 (1=black, 0=white)
    bw = img.load()
    out = []
    for y in range(img.height):
        row = [1 if bw[x, y] == 0 else 0 for x in range(img.width)]
        out.append(row)
    return out
"""
Basic Cat Printer BLE test: line feed only

- Connects to the printer using Bleak
- Sends a line feed (feed paper) command
- Prints debug output

Edit the DEVICE_NAME or DEVICE_ADDRESS as needed.
"""

import asyncio
import contextlib
import uuid
from bleak import BleakClient
from catprinter.cmds import cmd_feed_paper, CMD_GET_DEV_STATE, CMD_SET_QUALITY_200_DPI, bs, CMD_PRINT_TEXT, cmds_print_img, PRINT_WIDTH
from printer_lib.text_print import TextCanvas
def make_test_image():
    # Create a simple black bar image: 10 rows, all black
    img = [[1]*PRINT_WIDTH for _ in range(10)]
    return img

def make_text_image(text):
    # Render text to a 1-bit image using TextCanvas with a larger PF2 font
    canvas = TextCanvas(PRINT_WIDTH, font_path="fonts/Helvetica-24.pf2")
    img_bytes = next(canvas.puttext(text))
    img = []
    width = PRINT_WIDTH
    height = canvas.height
    for y in range(height):
        row = []
        for x in range(width):
            byte_index = (width * y + x) // 8
            bit_index = 7 - ((width * y + x) % 8)
            if img_bytes[byte_index] & (1 << bit_index):
                row.append(1)
            else:
                row.append(0)
        img.append(row)
    # Find last non-blank row
    last_ink_row = 0
    for y in range(len(img)):
        if any(img[y]):
            last_ink_row = y
    # Add a small margin after the last ink row
    margin = 8
    trimmed_img = img[:min(last_ink_row + 1 + margin, len(img))]
    return trimmed_img
def cmd_print_text(text):
    # CMD_PRINT_TEXT is the header, then ASCII bytes, then 0xff end
    # The original CMD_PRINT_TEXT is: bs([81, 120, -66, 0, 1, 0, 1, 7, -1])
    # But for actual text, we need to build a payload
    # Let's try a simple payload: header + text bytes + 0xff
    header = [81, 120, -66, 0, len(text)+1, 0, 1]  # 1 = text mode
    data = header + list(text.encode('ascii')) + [0xff]
    return bs(data)
def cmd_set_paper(amount, retract=False):
    # amount: number of steps to feed (positive integer, 1-255 typical)
    # retract: if True, will roll back instead of feed
    # The 7th byte (index 6) is the amount, 8th byte (index 7) is 0 for feed, 1 for retract
    # The checksum (index 8) must be recalculated
    arr = [81, 120, -95, 0, 2, 0, amount, 0, 0, -1]
    from catprinter.cmds import chk_sum
    arr[8] = chk_sum(bytearray(map(lambda v: v if v >= 0 else v & 0xff, arr)), 6, 2)
    return bs(arr)

def cmd_retract_paper(amount):
    arr = [81, 120, -96, 0, 2, 0, amount, 0, 0, -1]
    from catprinter.cmds import chk_sum
    arr[8] = chk_sum(bytearray(map(lambda v: v if v >= 0 else v & 0xff, arr)), 6, 2)
    return bs(arr)


# Hardcoded printer MAC address and model for testing
DEVICE_MAC = "CA:06:26:70:8B:06"
PRINTER_MODEL = "MX11"



TX_CHARACTERISTIC_UUID = "0000ae01-0000-1000-8000-00805f9b34fb"
RX_CHARACTERISTIC_UUID = "0000ae02-0000-1000-8000-00805f9b34fb"

async def main():
    print(f"Preparing command sequence for model {PRINTER_MODEL}...")
    commands = [
        ("GET_DEV_STATE", CMD_GET_DEV_STATE),
        ("SET_QUALITY_200_DPI", CMD_SET_QUALITY_200_DPI),
        ("PRINT_TEXT_AS_IMAGE", cmds_print_img(make_text_image("Hello World!"))),
        ("PRINT_CAT_IMAGE", cmds_print_img(load_and_prepare_image("cat.jpg"))),
        ("GET_DEV_STATE_2", CMD_GET_DEV_STATE),
    ]
    print(f"Connecting to printer at {DEVICE_MAC} ...")
    async with BleakClient(DEVICE_MAC) as client:
        print(f"Connected: {client.is_connected}; MTU: {client.mtu_size}")
        chunk_size = client.mtu_size - 3
        print(f"Subscribing to notifications on RX characteristic: {RX_CHARACTERISTIC_UUID}")
        notifications = []
        def notification_handler(sender, data):
            print(f"[NOTIFICATION] From {sender}: {data.hex()} | Raw: {data}")
            notifications.append((sender, data))
        await client.start_notify(RX_CHARACTERISTIC_UUID, notification_handler)
        for cmd_name, command in commands:
            print(f"\n--- Sending {cmd_name} ---")
            print(f"Command bytes: {command}")
            for i in range(0, len(command), chunk_size):
                chunk = command[i:i+chunk_size]
                print(f"Sending chunk {i//chunk_size+1}: {chunk.hex()} | Raw: {chunk}")
                await client.write_gatt_char(TX_CHARACTERISTIC_UUID, chunk)
            # No debug pause or input, just continue to next command
        print(f"\nReceived {len(notifications)} notifications in total.")
        for idx, (sender, data) in enumerate(notifications):
            print(f"Notification {idx+1}: From {sender}: {data.hex()} | Raw: {data}")
        await client.stop_notify(RX_CHARACTERISTIC_UUID)
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--text', type=str, help='Print the given text as an image')
    parser.add_argument('--image', type=str, help='Print the given image file (jpg/png)')
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')
    args = parser.parse_args()
    if args.help:
        print_usage()
    else:
        async def main_with_args():
            print(f"Preparing command sequence for model {PRINTER_MODEL}...")
            commands = [
                ("GET_DEV_STATE", CMD_GET_DEV_STATE),
                ("SET_QUALITY_200_DPI", CMD_SET_QUALITY_200_DPI),
            ]
            if args.text or not (args.text or args.image):
                text = args.text if args.text else "Hello World!"
                commands.append(("PRINT_TEXT_AS_IMAGE", cmds_print_img(make_text_image(text))))
            if args.image or not (args.text or args.image):
                image_file = args.image if args.image else "cat.jpg"
                commands.append(("PRINT_CAT_IMAGE", cmds_print_img(load_and_prepare_image(image_file))))
            commands.append(("GET_DEV_STATE_2", CMD_GET_DEV_STATE))
            print(f"Connecting to printer at {DEVICE_MAC} ...")
            async with BleakClient(DEVICE_MAC) as client:
                print(f"Connected: {client.is_connected}; MTU: {client.mtu_size}")
                chunk_size = client.mtu_size - 3
                print(f"Subscribing to notifications on RX characteristic: {RX_CHARACTERISTIC_UUID}")
                notifications = []
                def notification_handler(sender, data):
                    print(f"[NOTIFICATION] From {sender}: {data.hex()} | Raw: {data}")
                    notifications.append((sender, data))
                await client.start_notify(RX_CHARACTERISTIC_UUID, notification_handler)
                for cmd_name, command in commands:
                    print(f"\n--- Sending {cmd_name} ---")
                    print(f"Command bytes: {command}")
                    for i in range(0, len(command), chunk_size):
                        chunk = command[i:i+chunk_size]
                        print(f"Sending chunk {i//chunk_size+1}: {chunk.hex()} | Raw: {chunk}")
                        await client.write_gatt_char(TX_CHARACTERISTIC_UUID, chunk)
                print(f"\nReceived {len(notifications)} notifications in total.")
                for idx, (sender, data) in enumerate(notifications):
                    print(f"Notification {idx+1}: From {sender}: {data.hex()} | Raw: {data}")
                await client.stop_notify(RX_CHARACTERISTIC_UUID)
            print("Done.")
        asyncio.run(main_with_args())
