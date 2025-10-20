#!/usr/bin/env python3
"""
Test Cat-Printer inspired single-line chunking approach
"""

import asyncio
import logging
from mx11 import Printer

async def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')
    
    printer = Printer("CA:06:26:70:8B:06", log_level=logging.INFO)
    
    try:
        print("Connecting to printer...")
        await printer.connect()
        print("Connected successfully!")
        
        if not await printer.get_status():
            print("Printer not ready")
            return
            
        print("Testing CAT-PRINTER STYLE: Single-line chunking, speed=8...")
        await printer.print_image("buddha_small.jpg", extra_feed=15)
        print("Print completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await printer.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
