#!/usr/bin/env python3
"""
Main command-line interface for controlling the MX11 Thermal Printer.
"""


import asyncio
import argparse
import json
import logging
from mx11 import Printer
from PIL import ImageFont, ImageDraw
from image_convert import text_to_image
import os

CONFIG_FILE = "config.json"

def load_config():
    """Loads configuration from config.json, creating it if it doesn't exist."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Configuration file not found. Creating a default {CONFIG_FILE}...")
        default_config = {
            "mac_address": "XX:XX:XX:XX:XX:XX",
            "defaults": {
                "concentration": 65535,
                "speed": 60,
                "feed_lines": 20,
                "image_binarization": "floyd-steinberg"
            }
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

async def run(args, config):
    """Connects to the printer and executes the requested command."""
    log_level = getattr(logging, (args.loglevel or config.get('loglevel', 'WARNING')).upper(), logging.WARNING)
    logging.basicConfig(level=log_level, format='[%(levelname)s] %(name)s: %(message)s')
    # Set font options for text_to_image
    font_name = args.font or config.get('font', 'arial.ttf')
    font_size = args.fontsize or int(config.get('fontsize', 20))
    mac_address = args.mac or config.get("mac_address")
    if not mac_address or mac_address == "XX:XX:XX:XX:XX:XX":
        logging.error("Printer MAC address not configured. Please set it in config.json or use the --mac argument.")
        return
    printer = Printer(mac_address, log_level=log_level)
    try:
        await printer.connect()
        if not await printer.get_status():
            logging.error("Printer is not ready. Check paper and battery.")
            return
        if args.speed:
            await printer.set_speed(args.speed)
        if args.concentration:
            await printer.set_concentration(args.concentration)
        if args.image:
            await printer.print_image(
                args.image,
                energy=args.concentration or config['defaults']['concentration'],
                process=not args.raw
            )
        if args.textfile:
            with open(args.textfile, 'r') as f:
                text = f.read()
            img = text_to_image(text, font_name=font_name, font_size=font_size)
            img.save("text_as_image.png")
            await printer.print_image("text_as_image.png", energy=args.concentration or config['defaults']['concentration'])
        if args.feed:
            await printer.feed_paper(args.feed)
        if args.status:
            logging.info("Printer status check was successful.")
        if args.serial:
            await printer.get_serial_number()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if printer.client and printer.client.is_connected:
            await printer.disconnect()

def main():
    config = load_config()
    defaults = config.get("defaults", {})
    parser = argparse.ArgumentParser(description='MX11 Thermal Printer Control Script', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-m', '--mac', type=str, default=None,
                       help=f'Printer MAC address. Overrides the value in {CONFIG_FILE}.')
    parser.add_argument('--loglevel', type=str, default=None, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).')
    # --- Actions ---
    actions = parser.add_argument_group('Actions')
    actions.add_argument('-i', '--image', type=str, help='Path to an image file to print.')
    actions.add_argument('--raw', action='store_true', help='Send image as-is (no processing). Only for use with pre-converted 1-bit images.')
    actions.add_argument('-t', '--textfile', type=str, help='Path to a text file to print.')
    actions.add_argument('--feed', type=int, default=defaults.get('feed_lines'),
                        help=f'Feed paper by a specified number of lines (default: {defaults.get("feed_lines")}).')
    actions.add_argument('--status', action='store_true', help='Query and display the printer status.')
    actions.add_argument('--serial', action='store_true', help='Query and display the printer serial number.')
    actions.add_argument('--calibrate', action='store_true', help='Send label calibration command to the printer.')
    # --- Print Quality ---
    quality = parser.add_argument_group('Print Quality')
    quality.add_argument('-c', '--concentration', type=int, default=defaults.get('concentration'),
                         help=f'Print concentration/density (0-65535, default: {defaults.get("concentration")}).')
    quality.add_argument('-s', '--speed', type=int, default=defaults.get('speed'),
                         help=f'Print speed (default: {defaults.get("speed")}).')
    # --- Font Options ---
    font = parser.add_argument_group('Font Options')
    font.add_argument('--font', type=str, default=None, help='Font file name from C:\\Windows\\Fonts (e.g., arial.ttf, times.ttf). Default: arial.ttf')
    font.add_argument('--fontsize', type=int, default=None, help='Font size in points. Default: 20')
    args = parser.parse_args()
    if not any([args.image, args.textfile, args.feed, args.status, args.serial]):
        parser.print_help()
        print("\nError: No action specified. Please choose an action (e.g., --image, --feed).")
        return
    asyncio.run(run(args, config))

if __name__ == "__main__":
    main()