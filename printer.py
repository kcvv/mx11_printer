#!/usr/bin/env python3
"""
Consolidated Cat Printer Library
Single file containing all necessary functions for MX11 thermal printer
"""

import asyncio
import argparse
import io
from typing import Dict, Tuple
from PIL import Image
from bleak import BleakClient

# Constants
PRINT_WIDTH = 384
TX_CHARACTERISTIC_UUID = "0000ae01-0000-1000-8000-00805f9b34fb"
RX_CHARACTERISTIC_UUID = "0000ae02-0000-1000-8000-00805f9b34fb"

# ============================================================================
# PF2 Font Handling (from printer_lib/pf2.py)
# ============================================================================

def uint32be(b: bytes):
    return (b[0] << 24) + (b[1] << 16) + (b[2] << 8) + b[3]

def int32be(b: bytes):
    u = uint32be(b)
    return u - ((u >> 31 & 0b1) << 32)

def uint16be(b: bytes):
    return (b[0] << 8) + b[1]

def int16be(b: bytes):
    u = uint16be(b)
    return u - ((u >> 15 & 0b1) << 16)

class Character:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.x_offset = 0
        self.y_offset = 0
        self.device_width = 0
        self.bitmap_data = b''

    def get_bit(self, x, y):
        char_byte = (self.width * y + x) // 8
        char_bit = 7 - (self.width * y + x) % 8
        return self.bitmap_data[char_byte] & (0b1 << char_bit)

class CharacterS(Character):
    def __init__(self):
        super().__init__()
        self.scale = 1

    def get_bit(self, x, y):
        scale = self.scale
        width = self.width // scale
        x //= scale
        y //= scale
        char_byte = (width * y + x) // 8
        char_bit = 7 - (width * y + x) % 8
        return (self.bitmap_data[char_byte] & (0b1 << char_bit)) >> char_bit

class PF2:
    def __init__(self, file: io.BufferedIOBase, missing_character: str='?'):
        self.missing_character_code = ord(missing_character)
        self.broken = False
        self.data_io = io.BytesIO(file.read())
        file.close()
        
        if self.data_io.read(12) != b'FILE\x00\x00\x00\x04PFF2':
            self.broken = True
            return
            
        self.character_index = {}
        
        while True:
            name = self.data_io.read(4)
            if len(name) < 4:
                break
            data_length = int32be(self.data_io.read(4))
            
            if name == b'CHIX':
                for _ in range(data_length // 9):
                    code_point = int32be(self.data_io.read(4))
                    compression = self.data_io.read(1)[0]
                    offset = int32be(self.data_io.read(4))
                    self.character_index[code_point] = (compression, offset)
                continue
            elif name == b'DATA':
                self.data_io.seek(0)
                break
                
            data = self.data_io.read(data_length)
            if name == b'PTSZ':
                self.point_size = uint16be(data)
            elif name == b'MAXW':
                self.max_width = uint16be(data)
            elif name == b'MAXH':
                self.max_height = uint16be(data)
            elif name == b'ASCE':
                self.ascent = uint16be(data)
            elif name == b'DESC':
                self.descent = uint16be(data)

    def get_char(self, char: str):
        char_point = ord(char)
        info = self.character_index.get(char_point)
        if info is None:
            info = self.character_index[self.missing_character_code]
        
        _compression, offset = info
        self.data_io.seek(offset)
        char = Character()
        char.width = uint16be(self.data_io.read(2))
        char.height = uint16be(self.data_io.read(2))
        char.x_offset = int16be(self.data_io.read(2))
        char.y_offset = int16be(self.data_io.read(2))
        char.device_width = int16be(self.data_io.read(2))
        char.bitmap_data = self.data_io.read((char.width * char.height + 7) // 8)
        return char

    def __getitem__(self, char):
        return self.get_char(char)

class PF2S(PF2):
    def __init__(self, *args, scale: int=1, **kwargs):
        super().__init__(*args, **kwargs)
        if self.broken:
            return
        self.scale = scale
        self.point_size *= scale
        self.max_width *= scale
        self.max_height *= scale
        self.ascent *= scale
        self.descent *= scale

    def get_char(self, char):
        scale = self.scale
        char = super().get_char(char)
        chars = CharacterS()
        chars.scale = scale
        chars.width = char.width * scale
        chars.height = char.height * scale
        chars.device_width = char.device_width * scale
        chars.x_offset = char.x_offset * scale
        chars.y_offset = char.y_offset * scale
        chars.bitmap_data = char.bitmap_data
        return chars

# ============================================================================
# Text Canvas (from printer_lib/text_print.py)
# ============================================================================

class TextCanvas:
    def __init__(self, width, *, font_path='fonts/Helvetica-24.pf2', scale=1):
        self.broken = False
        self.canvas = None
        try:
            font_data_io = open(font_path.strip("'\""), 'rb')
            self.pf2 = PF2S(font_data_io, scale=scale)
        except FileNotFoundError:
            self.broken = True
            return
            
        if self.pf2.broken:
            self.broken = True
            return
            
        self.width = width
        self.scale = scale
        self.height = self.pf2.max_height + self.pf2.descent
        self.flush_canvas()

    def flush_canvas(self):
        if self.canvas is None:
            pbm_data = None
        else:
            pbm_data = bytearray(self.canvas)
        self.canvas = bytearray(self.width * self.height // 8)
        return pbm_data

    def puttext(self, text):
        text = text.replace('\t', ' ' * 4)
        canvas_length = len(self.canvas)
        pf2 = self.pf2
        current_width = 0
        characters = {}
        yielded = False
        
        for s in text:
            if s not in characters:
                characters[s] = pf2[s]
        
        for i, s in enumerate(text):
            char = characters[s]
            if s == '\n' or current_width + char.width > self.width:
                yield self.flush_canvas()
                yielded = True
                current_width = 0
                if s in ' \n':
                    continue
                    
            if ord(s) in range(0x00, 0x20):
                continue
                
            for x in range(char.width):
                for y in range(char.height):
                    target_x = x + char.x_offset
                    target_y = pf2.ascent + (y - char.height) - char.y_offset
                    canvas_byte = (self.width * target_y + current_width + target_x) // 8
                    canvas_bit = 7 - (self.width * target_y + current_width + target_x) % 8
                    
                    if 0 <= canvas_byte < canvas_length:
                        self.canvas[canvas_byte] |= char.get_bit(x, y) << canvas_bit
                        
            current_width += char.device_width
            
        if not yielded:
            yield self.flush_canvas()

# ============================================================================
# Printer Commands (from catprinter/cmds.py)
# ============================================================================

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

# Printer commands
CMD_GET_DEV_STATE = bs([81, 120, -93, 0, 1, 0, 0, 0, -1])
CMD_SET_QUALITY_200_DPI = bs([81, 120, -92, 0, 1, 0, 50, -98, -1])
CMD_LATTICE_START = bs([81, 120, -90, 0, 11, 0, -86, 85, 23, 56, 68, 95, 95, 95, 68, 56, 44, -95, -1])
CMD_LATTICE_END = bs([81, 120, -90, 0, 11, 0, -86, 85, 23, 0, 0, 0, 0, 0, 0, 0, 23, 17, -1])
CMD_SET_PAPER = bs([81, 120, -95, 0, 2, 0, 48, 0, -7, -1])

def cmd_feed_paper(how_much):
    b_arr = bs([81, 120, -67, 0, 1, 0, how_much & 0xff, 0, 0xff])
    b_arr[7] = chk_sum(b_arr, 6, 1)
    return bs(b_arr)

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

def cmds_print_img(img, energy: int = 0xffff):
    print(f"Debug: Creating print commands for {len(img)} rows")
    data = CMD_GET_DEV_STATE + CMD_SET_QUALITY_200_DPI + cmd_set_energy(energy) + cmd_apply_energy() + CMD_LATTICE_START
    for row in img:
        data += cmd_print_row(row)
    data += cmd_feed_paper(8) + CMD_LATTICE_END + CMD_GET_DEV_STATE
    print(f"Debug: Total command data: {len(data)} bytes")
    return data

# ============================================================================
# Image Processing Functions
# ============================================================================

def load_and_prepare_image(path):
    img = Image.open(path).convert('L')
    new_height = int(img.height * PRINT_WIDTH / img.width)
    img = img.resize((PRINT_WIDTH, new_height), Image.LANCZOS)
    img = img.convert('1')
    
    bw = img.load()
    out = []
    for y in range(img.height):
        row = [1 if bw[x, y] == 0 else 0 for x in range(img.width)]
        out.append(row)
    return out

def make_text_image(text, font_path='fonts/Helvetica-24.pf2'):
    canvas = TextCanvas(PRINT_WIDTH, font_path=font_path)
    if canvas.broken:
        raise FileNotFoundError(f"Font file not found: {font_path}")
    
    print(f"Debug: Canvas height={canvas.height}, text length={len(text)}")
    img_bytes = next(canvas.puttext(text))
    print(f"Debug: Generated {len(img_bytes)} bytes")
    img = []
    width = PRINT_WIDTH
    height = canvas.height
    
    for y in range(height):
        row = []
        for x in range(width):
            byte_index = (width * y + x) // 8
            bit_index = 7 - ((width * y + x) % 8)
            if byte_index < len(img_bytes) and img_bytes[byte_index] & (1 << bit_index):
                row.append(1)
            else:
                row.append(0)
        img.append(row)
    
    # Trim to last ink row + margin
    last_ink_row = 0
    for y in range(len(img)):
        if any(img[y]):
            last_ink_row = y
    
    margin = 8
    trimmed_img = img[:min(last_ink_row + 1 + margin, len(img))]
    print(f"Debug: Final image {len(trimmed_img)} rows, last ink at row {last_ink_row}")
    return trimmed_img

# ============================================================================
# Main Printer Class
# ============================================================================

class CatPrinter:
    def __init__(self, device_mac, font_path='fonts/Helvetica-24.pf2'):
        self.device_mac = device_mac
        self.font_path = font_path
        
    async def print_text(self, text):
        img = make_text_image(text, self.font_path)
        await self._send_to_printer(cmds_print_img(img))
        
    async def print_image(self, image_path):
        img = load_and_prepare_image(image_path)
        await self._send_to_printer(cmds_print_img(img))
        
    async def _send_to_printer(self, commands):
        print(f"Connecting to {self.device_mac}...")
        try:
            async with BleakClient(self.device_mac) as client:
                print(f"✅ Connected: MTU {client.mtu_size}")
                chunk_size = client.mtu_size - 3
                
                notifications = []
                def notification_handler(sender, data):
                    print(f"[RX] {data.hex()}")
                    notifications.append((sender, data))
                    
                await client.start_notify(RX_CHARACTERISTIC_UUID, notification_handler)
                
                print(f"Sending {len(commands)} bytes in chunks of {chunk_size}...")
                for i in range(0, len(commands), chunk_size):
                    chunk = commands[i:i+chunk_size]
                    await client.write_gatt_char(TX_CHARACTERISTIC_UUID, chunk)
                    await asyncio.sleep(0.02)  # Small delay between chunks
                    
                await asyncio.sleep(1)  # Wait for printer to process
                await client.stop_notify(RX_CHARACTERISTIC_UUID)
        except Exception as e:
            raise Exception(f"Bluetooth error: {e}")

# ============================================================================
# Command Line Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Cat Printer Test Utility')
    parser.add_argument('--text', type=str, help='Print the given text as an image')
    parser.add_argument('--file', type=str, help='Print text from file')
    parser.add_argument('--stdin', action='store_true', help='Read text from stdin')
    parser.add_argument('--image', type=str, help='Print the given image file (jpg/png)')
    parser.add_argument('--font', type=str, default='fonts/Helvetica-24.pf2', 
                       help='Font file to use for text rendering (default: fonts/Helvetica-24.pf2)')
    parser.add_argument('--mac', type=str, default='CA:06:26:70:8B:06',
                       help='Printer MAC address (default: CA:06:26:70:8B:06)')
    parser.add_argument('--test', action='store_true', help='Test mode - generate image without printing')
    parser.add_argument('--list-fonts', action='store_true', help='List available fonts')
    
    args = parser.parse_args()
    
    if args.list_fonts:
        import os
        if os.path.exists('fonts'):
            fonts = [f for f in os.listdir('fonts') if f.endswith('.pf2')]
            print("Available fonts:")
            for font in sorted(fonts):
                print(f"  fonts/{font}")
        else:
            print("No fonts directory found")
        return
    
    def get_text_content():
        if args.stdin:
            import sys
            return sys.stdin.read().strip()
        elif args.file:
            with open(args.file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        elif args.text:
            return args.text
        else:
            return "Hello World!"
    
    async def run():
        if args.test:
            if args.text or args.file or args.stdin or not (args.text or args.file or args.stdin or args.image):
                text = get_text_content()
                print(f"Generating text image: {text[:50]}{'...' if len(text) > 50 else ''} (font: {args.font})")
                try:
                    img = make_text_image(text, args.font)
                    print(f"✅ Text image generated: {len(img)} rows")
                except Exception as e:
                    print(f"❌ Error: {e}")
            return
        
        printer = CatPrinter(args.mac)
        
        try:
            if args.text or args.file or args.stdin or not (args.text or args.file or args.stdin or args.image):
                text = get_text_content()
                print(f"Printing text: {text[:50]}{'...' if len(text) > 50 else ''} (font: {args.font})")
                printer.font_path = args.font
                await printer.print_text(text)
                
            if args.image or not (args.text or args.file or args.stdin or args.image):
                image_file = args.image if args.image else "cat.jpg"
                print(f"Printing image: {image_file}")
                await printer.print_image(image_file)
                
            print("Done.")
        except FileNotFoundError as e:
            print(f"❌ File not found: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 Try: --test flag to test without printer")
    
    asyncio.run(run())

if __name__ == "__main__":
    main()