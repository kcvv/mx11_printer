#!/usr/bin/env python3
"""
Test script to compare different chunking methods for fixing streaking issues.
"""

import asyncio
import logging
from mx11 import Printer

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_chunking_methods():
    """Test different chunking approaches to fix streaking."""
    
    # Replace with your printer's MAC address
    printer_address = "CA:06:26:70:8B:06"
    
    printer = Printer(printer_address, log_level=logging.INFO)
    
    try:
        print("Connecting to printer...")
        await printer.connect()
        
        # Check printer status
        status = await printer.get_status()
        if not status:
            print("Printer not ready or not V5G family")
            return
            
        # Test image path
        test_image = "buddha_small.jpg"
        
        print("\n=== Testing Original Method (4-row chunks) ===")
        # Temporarily restore original chunk size for comparison
        img = printer.load_and_prepare_image(test_image)
        # Use original print_image method (now with chunk_size=50)
        await printer.print_image(img, extra_feed=20)
        
        print("\n=== Testing No-Chunk Method (Anti-Streaking) ===")
        img = printer.load_and_prepare_image(test_image)
        await printer.print_image_no_chunks(img, extra_feed=20)
        
        print("\nTest completed! Compare the prints to see which has less streaking.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await printer.disconnect()

if __name__ == "__main__":
    asyncio.run(test_chunking_methods())
