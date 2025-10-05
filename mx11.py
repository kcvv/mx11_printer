# c:\Users\Venky\Downloads\Cat-Printer-main\mx11_printer\mx11.py

"""
Python library for controlling MX11 (and other V5G-family) thermal printers.
Features reverse-engineered from the Fun Print Android application.
"""


import asyncio
import io
import logging
from dataclasses import dataclass
from PIL import Image
from bleak import BleakClient
import numpy as np

# Constants
PRINT_WIDTH = 384
TX_CHARACTERISTIC_UUID = "0000ae01-0000-1000-8000-00805f9b34fb" # Write
RX_CHARACTERISTIC_UUID = "0000ae02-0000-1000-8000-00805f9b34fb" # Notify

# --- Commands from APK Analysis (V5G Family) ---
CMD_GET_STATUS = b'\x51\x78\xa3\x00\x01\x00\x00\x00\xff'
CMD_GET_SERIAL = b'\x51\x78\xa8\x00\x01\x00\x00\x00\xff'
CMD_SET_SPEED_PREFIX = b'\x51\x78\xf1\x00\x01\x00'
CMD_SET_CONCENTRATION_PREFIX = b'\x51\x78\xf2\x00\x02\x00'
CMD_LABEL_CALIBRATE_PREFIX = b'\x51\x78\xf0\x00\x03\x00'
CMD_FEED_PAPER_PREFIX = b'\x51\x78\xf0\x00\x02\x00'
CMD_SUFFIX = b'\xff'

# --- Commands from test-copy.py ---
CMD_SET_QUALITY_200_DPI = b'\x51\x78\xa4\x00\x01\x00\x32\x9e\xff'
CMD_LATTICE_START = b'\x51\x78\xa6\x00\x0b\x00\xaa\x55\x17\x38\x44\x5f\x5f\x5f\x44\x38\x2c\xa1\xff'
CMD_LATTICE_END = b'\x51\x78\xa6\x00\x0b\x00\xaa\x55\x17\x00\x00\x00\x00\x00\x00\x00\x17\x11\xff'
CMD_SET_PAPER = b'\x51\x78\xa1\x00\x02\x00\x30\x00\xf9\xff'

# =====================
# EXPERIMENTAL V5G-FAMILY COMMANDS (from CatPrinterBLE/MXW01)
# These are for testing only. Remove if not useful for MX11.
# =====================
CMD_EJECT_PAPER = b'\x51\x78\xa3\x00\x02\x00'  # + 2 bytes little-endian line count + 0xff
CMD_RETRACT_PAPER = b'\x51\x78\xa4\x00\x02\x00'  # + 2 bytes little-endian line count + 0xff
CMD_QUERY_COUNT = b'\x51\x78\xa7\x00\x01\x00\x00\xff'
CMD_BATTERY_LEVEL = b'\x51\x78\xab\x00\x01\x00\x00\xff'
CMD_GET_PRINT_TYPE = b'\x51\x78\xb0\x00\x01\x00\x00\xff'
CMD_GET_VERSION = b'\x51\x78\xb1\x00\x01\x00\x00\xff'

@dataclass
class PrinterProfile:
    """Holds settings for a specific printer model group."""
    speed: int
    concentration: int
    supports_labels: bool

# Profile for MX series printers based on V5G group in the APK
V5G_PROFILE = PrinterProfile(
    speed=60,
    concentration=110, # A good default starting value
    supports_labels=True
)

def to_unsigned_byte(val):
    return val if val >= 0 else val & 0xff

def bs(lst):
    return bytearray(map(to_unsigned_byte, lst))

CHECKSUM_TABLE = bs([
    0, 7, 14, 9, 28, 27, 18, 21, 56, 63, 54, 49, 36, 35, 42, 45, 112, 119, 126, 121,
    108, 107, 98, 101, 72, 79, 70, 65, 84, 83, 90, 93, -32, -25, -18, -23, -4, -5,
    -14, -11, -40, -33, -42, -47, -60, -61, -54, -51, -112, -105, -98, -103, -116,
    -117, -126, -123, -88, -81, -90, -95, -76, -77, -70, -67, -57, -64, -55, -50,
    -37, -36, -43, -46, -1, -8, -15, -10, -29, -28, -19, -22, -73, -80, -71, -66,
    -85, -84, -91, -94, -113, -120, -127, -122, -109, -108, -99, -102, 39, 32, 41,
    46, 59, 60, 53, 50, 31, 24, 17, 22, 3, 4, 13, 10, 87, 80, 89, 94, 75, 76, 69, 66,
    111, 104, 97, 102, 115, 116, 125, 122, -119, -114, -121, -128, -107, -110, -101,
    -100, -79, -74, -65, -72, -83, -86, -93, -92, -7, -2, -9, -16, -27, -30, -21, -20,
    -63, -58, -49, -56, -35, -38, -45, -44, 105, 110, 103, 96, 117, 114, 123, 124, 81,
    86, 95, 88, 77, 74, 67, 68, 25, 30, 23, 16, 5, 2, 11, 12, 33, 38, 47, 40, 61, 58,
    51, 52, 78, 73, 64, 71, 82, 85, 92, 91, 118, 113, 120, 127, 106, 109, 100, 99, 62,
    57, 48, 55, 34, 37, 44, 43, 6, 1, 8, 15, 26, 29, 20, 19, -82, -87, -96, -89, -78,
    -75, -68, -69, -106, -111, -104, -97, -118, -115, -124, -125, -34, -39, -48, -41,
    -62, -59, -52, -53, -26, -31, -24, -17, -6, -3, -12, -13,
])

def chk_sum(b_arr, i, i2):
    b2 = 0
    for i3 in range(i, i + i2):
        b2 = CHECKSUM_TABLE[(b2 ^ b_arr[i3]) & 0xff]
    return b2

def cmd_set_energy(val):
    b_arr = bs([81, 120, -81, 0, 2, 0, (val >> 8) & 0xff, val & 0xff, 0, 0xff])
    b_arr[8] = chk_sum(b_arr, 6, 2)
    return bs(b_arr)

def cmd_apply_energy():
    b_arr = bs([81, 120, -66, 0, 1, 0, 1, 0, 0xff])
    b_arr[7] = chk_sum(b_arr, 6, 1)
    return bs(b_arr)

def encode_run_length_repetition(n, val):
    res = []
    while n > 0x7f:
        res.append(0x7f | (val << 7))
        n -= 0x7f
    if n > 0:
        res.append((val << 7) | n)
    return res

def run_length_encode(img_row):
    res = []
    count = 0
    last_val = -1
    for val in img_row:
        if val == last_val:
            count += 1
        else:
            res.extend(encode_run_length_repetition(count, last_val))
            count = 1
        last_val = val
    if count > 0:
        res.extend(encode_run_length_repetition(count, last_val))
    return res

def byte_encode(img_row):
    res = []
    for chunk_start in range(0, len(img_row), 8):
        byte = 0
        for bit_index in range(8):
            if chunk_start + bit_index < len(img_row) and img_row[chunk_start + bit_index]:
                byte |= 1 << bit_index
        res.append(byte)
    return res

def cmd_print_row(img_row):
    encoded_img = run_length_encode(img_row)
    
    if len(encoded_img) > PRINT_WIDTH // 8:
        encoded_img = byte_encode(img_row)
        b_arr = bs([81, 120, -94, 0, len(encoded_img), 0] + encoded_img + [0, 0xff])
        b_arr[-2] = chk_sum(b_arr, 6, len(encoded_img))
        return b_arr
    
    b_arr = bs([81, 120, -65, 0, len(encoded_img), 0] + encoded_img + [0, 0xff])
    b_arr[-2] = chk_sum(b_arr, 6, len(encoded_img))
    return b_arr


class Printer:
    async def calibrate_label(self):
        """Send the label calibration command to the printer."""
        self.logger.info("Sending label calibration command...")
        try:
            response = await self._write_with_response(CMD_LABEL_CALIBRATE_PREFIX)
            self.logger.info(f"Calibration response: {response.hex()}")
            return response
        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            return None
    def __init__(self, address, log_level=logging.WARNING):
        self.address = address
        self.client = None
        self.profile = V5G_PROFILE # Assume V5G profile for MX11
        self.logger = logging.getLogger(f"Printer[{self.address}]")
        self.logger.setLevel(log_level)
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    async def connect(self):
        self.client = BleakClient(self.address)
        await self.client.connect()
        self.logger.info(f"Connected to {self.address}")

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            self.logger.info(f"Disconnected from {self.address}")

    async def _write(self, data: bytes, response: bool = False):
        """Logs and writes data to the printer."""
        self.logger.debug(f"TX: {data.hex()}")
        await self.client.write_gatt_char(TX_CHARACTERISTIC_UUID, data, response=response)

    async def _write_with_response(self, data: bytes):
        """Writes data, logs it, and waits for a single notification, which is also logged."""
        future = asyncio.get_event_loop().create_future()
        def notification_handler(sender, response_data):
            self.logger.debug(f"RX: {response_data.hex()}")
            if not future.done():
                future.set_result(response_data)
        await self.client.start_notify(RX_CHARACTERISTIC_UUID, notification_handler)
        await self._write(data)
        try:
            response = await asyncio.wait_for(future, timeout=5.0)
        finally:
            await self.client.stop_notify(RX_CHARACTERISTIC_UUID)
        return response

    async def get_status(self):
        """Queries the printer status. This is a good way to test if it's a V5G printer."""
        self.logger.info("Querying printer status...")
        try:
            response = await self._write_with_response(CMD_GET_STATUS)
            self.logger.debug(f"Status response: {response.hex()}")
            if len(response) < 10:
                self.logger.warning("Received a short status response. May not be a V5G printer.")
                return False
            status_byte = response[6]
            if status_byte == 0x00:
                self.logger.info("Status: OK")
                return True
            if status_byte & 0b00000001:
                self.logger.error("Error: No paper")
            if status_byte & 0b00000100:
                self.logger.error("Error: Overheating")
            if status_byte & 0b00001000:
                self.logger.error("Error: Low battery")
            return False
        except asyncio.TimeoutError:
            self.logger.error("Status query timed out. The printer did not respond. It might not be a V5G-family device.")
            return False

    async def get_serial_number(self):
        """Queries the printer for its serial number."""
        self.logger.info("Querying serial number...")
        try:
            response = await self._write_with_response(CMD_GET_SERIAL)
            serial = response[6:-2].decode('ascii')
            self.logger.info(f"Serial Number: {serial}")
            return serial
        except asyncio.TimeoutError:
            self.logger.error("Serial number query timed out.")
            return None
        except Exception as e:
            self.logger.error(f"Could not decode serial number: {e}")
            return None

    async def set_speed(self, speed: int):
        """Sets the print speed."""
        command = CMD_SET_SPEED_PREFIX + speed.to_bytes(1, 'big') + CMD_SUFFIX
        await self._write(command)

    async def set_concentration(self, concentration: int = 0xffff):
        """Sets the print concentration/density."""
        b_arr = bs([81, 120, -81, 0, 2, 0, (concentration >> 8) & 0xff, concentration & 0xff, 0, 0xff])
        b_arr[8] = chk_sum(b_arr, 6, 2)
        await self._write(bs(b_arr))

    async def feed_paper(self, lines: int = 1):
        """Sends a command to feed the paper by a specified number of lines/units."""
        self.logger.info(f"Sending command to feed paper by {lines} units...")
        command = self._cmd_feed_paper(lines)
        await self._write(command)

    def _cmd_feed_paper(self, lines: int = 1):
        """Returns the command to feed the paper by a specified number of lines/units."""
        b_arr = bs([81, 120, -95, 0, 2, 0, lines & 0xff, 0, 0, 0xff])
        b_arr[8] = chk_sum(b_arr, 6, 2)
        return b_arr

    def load_and_prepare_image(self, path, binarization='floyd-steinberg'):
        img = Image.open(path).convert('L')
        new_height = int(img.height * PRINT_WIDTH / img.width)
        img = img.resize((PRINT_WIDTH, new_height), Image.LANCZOS)
        
        img_array = np.array(img)
        
        if binarization == 'floyd-steinberg':
            img_array = self.floyd_steinberg_dither(img_array.copy())
            binary = img_array > 127
        else:
            binary = img_array > 127
        
        out = []
        for y in range(binary.shape[0]):
            row = [1 if not binary[y, x] else 0 for x in range(binary.shape[1])]
            out.append(row)
        return out

    def floyd_steinberg_dither(self, img):
        h, w = img.shape
        def adjust_pixel(y, x, delta):
            if y < 0 or y >= h or x < 0 or x >= w:
                return
            img[y][x] = min(255, max(0, img[y][x] + delta))
        
        for y in range(h):
            for x in range(w):
                new_val = 255 if img[y][x] > 127 else 0
                err = img[y][x] - new_val
                img[y][x] = new_val
                adjust_pixel(y, x + 1, err * 7/16)
                adjust_pixel(y + 1, x - 1, err * 3/16)
                adjust_pixel(y + 1, x, err * 5/16)
                adjust_pixel(y + 1, x + 1, err * 1/16)
        return img

    async def print_image(self, image_path, energy: int = 0xffff, extra_feed: int = 0, process: bool = True):
        if not self.client or not self.client.is_connected:
            self.logger.error("Not connected to printer.")
            return
        self.logger.info("--- Starting Print Job ---")
        if process:
            img = self.load_and_prepare_image(image_path)
        else:
            from PIL import Image
            import numpy as np
            img = Image.open(image_path)
            if img.mode != '1':
                img = img.convert('1')
            if img.width != PRINT_WIDTH:
                raise ValueError(f"Image width must be {PRINT_WIDTH} pixels, got {img.width}.")
            img_array = np.array(img, dtype=np.uint8)
            # Convert to 0/1 as expected by cmd_print_row
            binary = (img_array == 0)
            out = []
            for y in range(binary.shape[0]):
                row = [1 if binary[y, x] else 0 for x in range(binary.shape[1])]
                # Validate row values
                if not all(v in (0, 1) for v in row):
                    raise ValueError(f"Row contains non-binary values: {row}")
                out.append(row)
            img = out
        commands = CMD_GET_STATUS + CMD_SET_QUALITY_200_DPI + cmd_set_energy(energy) + cmd_apply_energy() + CMD_LATTICE_START
        for row in img:
            commands += cmd_print_row(row)
        feed_amount = 8 + extra_feed
        commands += self._cmd_feed_paper(feed_amount) + CMD_LATTICE_END + CMD_GET_STATUS
        chunk_size = 20
        for i in range(0, len(commands), chunk_size):
            chunk = commands[i:i+chunk_size]
            await self._write(chunk, response=False)
            await asyncio.sleep(0.02)
        self.logger.info("--- Print Job Finished ---")

    async def print_image_4bpp(self, image_path, intensity: int = 100, max_height: int = 1000):
        """EXPERIMENTAL: Print a grayscale image in 4bpp mode (if supported by printer). Limits height to max_height px."""
        if not self.client or not self.client.is_connected:
            self.logger.error("Not connected to printer.")
            return
        self.logger.info(f"--- Starting 4bpp Grayscale Print Job (EXPERIMENTAL, max height {max_height}) ---")
        # Load and resize image
        img = Image.open(image_path).convert('L')
        new_height = int(img.height * PRINT_WIDTH / img.width)
        img = img.resize((PRINT_WIDTH, new_height), Image.LANCZOS)
        # Limit height if needed
        if img.height > max_height:
            self.logger.info(f"Cropping image from {img.height} to {max_height} pixels height.")
            img = img.crop((0, 0, PRINT_WIDTH, max_height))
        # Ensure width is exactly 384 and even
        if img.width != PRINT_WIDTH:
            img = img.resize((PRINT_WIDTH, img.height), Image.LANCZOS)
        if img.width % 2 != 0:
            # Pad one column if odd
            img = img.crop((0, 0, img.width - 1, img.height))
        arr = np.array(img, dtype=np.uint8)
        # Quantize to 16 levels (4bpp)
        arr4 = (arr / 16).astype(np.uint8)
        arr4 = np.clip(arr4, 0, 15)
        # Pack two 4bpp pixels per byte
        packed = bytearray()
        for row in arr4:
            if len(row) % 2 != 0:
                row = np.append(row, 0)  # pad to even
            for i in range(0, len(row), 2):
                hi = int(row[i]) & 0x0F
                lo = int(row[i+1]) & 0x0F
                val = (hi << 4) | lo
                if not (0 <= val <= 255):
                    self.logger.error(f"4bpp pack error: hi={hi}, lo={lo}, val={val}, row[{i}]={row[i]}, row[{i+1}]={row[i+1]}")
                    raise ValueError(f"Packed byte out of range: {val}")
                packed.append(val)
        # Build command (based on CatPrinterBLE logic)
        line_count = arr4.shape[0]
        bytes_per_line = PRINT_WIDTH // 2
        print_cmd = bytearray([0x51, 0x78, 0xa9, 0x00, 0x04, 0x00,
                               line_count & 0xFF, (line_count >> 8) & 0xFF, 0x30, 0x02, 0xff])
        await self._write(bytearray([0x51, 0x78, 0xa2, 0x00, 0x01, 0x00, intensity, 0xff]))
        await self._write(print_cmd)
        for i in range(line_count):
            start = i * bytes_per_line
            end = start + bytes_per_line
            await self._write(packed[start:end])
        await self._write(bytearray([0x51, 0x78, 0xad, 0x00, 0x01, 0x00, 0x00, 0xff]))
        self.logger.info("--- 4bpp Grayscale Print Job Finished ---")

    async def test_print_minimal_4bpp(self):
        """Diagnostic: Try to print a tiny 4bpp image (8 lines, all mid-gray) to test protocol support."""
        if not self.client or not self.client.is_connected:
            self.logger.error("Not connected to printer.")
            return
        self.logger.info("--- Diagnostic: Sending minimal 4bpp print job (8 lines, mid-gray) ---")
        width = PRINT_WIDTH
        height = 8
        # 4bpp mid-gray = 0x8
        row = [0x8] * width
        arr4 = np.array([row] * height, dtype=np.uint8)
        # Pack two 4bpp pixels per byte
        packed = bytearray()
        for row in arr4:
            for i in range(0, len(row), 2):
                hi = int(row[i]) & 0x0F
                lo = int(row[i+1]) & 0x0F
                val = (hi << 4) | lo
                packed.append(val)
        line_count = height
        bytes_per_line = width // 2
        print_cmd = bytearray([0x51, 0x78, 0xa9, 0x00, 0x04, 0x00,
                               line_count & 0xFF, (line_count >> 8) & 0xFF, 0x30, 0x02, 0xff])
        await self._write(bytearray([0x51, 0x78, 0xa2, 0x00, 0x01, 0x00, 100, 0xff]))
        await self._write(print_cmd)
        for i in range(line_count):
            start = i * bytes_per_line
            end = start + bytes_per_line
            await self._write(packed[start:end])
        await self._write(bytearray([0x51, 0x78, 0xad, 0x00, 0x01, 0x00, 0x00, 0xff]))
        self.logger.info("--- Diagnostic 4bpp print job sent ---")

    # =====================
    # EXPERIMENTAL V5G-FAMILY COMMANDS (from CatPrinterBLE/MXW01)
    # =====================
    async def eject_paper(self, lines: int):
        """[EXPERIMENTAL] Ejects the paper by a specified number of lines."""
        self.logger.info(f"[EXPERIMENTAL] Ejecting paper by {lines} lines...")
        cmd = CMD_EJECT_PAPER + lines.to_bytes(2, 'little') + b'\xff'
        await self._write(cmd)

    async def retract_paper(self, lines: int):
        """[EXPERIMENTAL] Retracts the paper by a specified number of lines."""
        self.logger.info(f"[EXPERIMENTAL] Retracting paper by {lines} lines...")
        cmd = CMD_RETRACT_PAPER + lines.to_bytes(2, 'little') + b'\xff'
        await self._write(cmd)

    async def query_count(self):
        """[EXPERIMENTAL] Query count command (purpose unclear)."""
        self.logger.info("[EXPERIMENTAL] Sending query count command...")
        await self._write_with_response(CMD_QUERY_COUNT)

    async def get_battery_level(self):
        """[EXPERIMENTAL] Query battery level."""
        self.logger.info("[EXPERIMENTAL] Querying battery level...")
        await self._write_with_response(CMD_BATTERY_LEVEL)

    async def get_print_type(self):
        """[EXPERIMENTAL] Query print type (pressure/density)."""
        self.logger.info("[EXPERIMENTAL] Querying print type...")
        await self._write_with_response(CMD_GET_PRINT_TYPE)

    async def get_version(self):
        """[EXPERIMENTAL] Query firmware version."""
        self.logger.info("[EXPERIMENTAL] Querying firmware version...")
        await self._write_with_response(CMD_GET_VERSION)

    async def print_device_info(self):
        """[EXPERIMENTAL] Print BLE device info (not implemented, placeholder)."""
        self.logger.info("[EXPERIMENTAL] Device info not implemented in Python version.")
