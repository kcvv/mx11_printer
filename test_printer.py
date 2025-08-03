#!/usr/bin/env python3
"""
Simple test script for the consolidated printer.py
"""

import asyncio
from printer import CatPrinter

async def main():
    # Initialize printer with default font
    printer = CatPrinter("CA:06:26:70:8B:06")
    
    # Print some text
    await printer.print_text("Hello from consolidated printer!")
    
    # Print an image (if cat.jpg exists)
    try:
        await printer.print_image("cat.jpg")
    except FileNotFoundError:
        print("cat.jpg not found, skipping image print")

if __name__ == "__main__":
    asyncio.run(main())