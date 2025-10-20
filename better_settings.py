#!/usr/bin/env python3
"""
Better settings helper for existing printer.py
Usage: python better_settings.py [speed] [darkness]
"""

import sys

# Speed settings
SPEED_MAP = {'fast': 1, 'medium': 2, 'slow': 3}

# Darkness to concentration mapping (0-100 -> 100-150)
def darkness_to_concentration(darkness):
    if isinstance(darkness, str):
        presets = {'light': 25, 'medium': 50, 'dark': 75, 'max': 100}
        darkness = presets.get(darkness.lower(), 50)
    return int(100 + (max(0, min(100, int(darkness))) * 50 / 100))

def main():
    if len(sys.argv) < 2:
        print("Usage examples:")
        print("python better_settings.py medium dark")
        print("python better_settings.py fast 80")
        print("python better_settings.py slow light")
        print("\nSpeed: fast/medium/slow")
        print("Darkness: light/medium/dark/max or 0-100")
        return
    
    speed = sys.argv[1] if len(sys.argv) > 1 else 'medium'
    darkness = sys.argv[2] if len(sys.argv) > 2 else 'medium'
    
    speed_val = SPEED_MAP.get(speed.lower(), 2)
    concentration_val = darkness_to_concentration(darkness)
    
    print(f"Settings for: speed={speed}, darkness={darkness}")
    print(f"Use with printer.py:")
    print(f"--speed {speed_val} --concentration {concentration_val}")

if __name__ == "__main__":
    main()
