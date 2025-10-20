#!/usr/bin/env python3
"""
Improved MX11 settings based on Fun Print analysis
"""

# Speed settings (fast/medium/slow)
SPEED_SETTINGS = {
    'fast': 1,
    'medium': 2, 
    'slow': 3
}

# Darkness settings (0-100) mapped to MX11 values
# Based on Fun Print optimal values: low=100, middle=130, high=150
def darkness_to_mx11(darkness_percent):
    """Convert 0-100 darkness to MX11 concentration value"""
    if darkness_percent < 0:
        darkness_percent = 0
    elif darkness_percent > 100:
        darkness_percent = 100
    
    # Map 0-100 to Fun Print range 100-150
    return int(100 + (darkness_percent * 50 / 100))

# Preset darkness levels
DARKNESS_PRESETS = {
    'light': 25,    # -> 112 MX11 value
    'medium': 50,   # -> 125 MX11 value  
    'dark': 75,     # -> 137 MX11 value
    'max': 100      # -> 150 MX11 value
}

def get_speed_value(speed_name):
    """Get MX11 speed value from name"""
    return SPEED_SETTINGS.get(speed_name.lower(), 2)  # default medium

def get_darkness_value(darkness):
    """Get MX11 darkness value from percentage or preset name"""
    if isinstance(darkness, str):
        # Handle preset names
        if darkness.lower() in DARKNESS_PRESETS:
            return darkness_to_mx11(DARKNESS_PRESETS[darkness.lower()])
        else:
            raise ValueError(f"Unknown darkness preset: {darkness}")
    else:
        # Handle numeric percentage
        return darkness_to_mx11(darkness)

# Test the mappings
if __name__ == "__main__":
    print("=== Speed Settings ===")
    for name, value in SPEED_SETTINGS.items():
        print(f"{name:8}: {value}")
    
    print("\n=== Darkness Presets ===")
    for name, percent in DARKNESS_PRESETS.items():
        mx11_val = darkness_to_mx11(percent)
        print(f"{name:8}: {percent}% -> MX11 value {mx11_val}")
    
    print("\n=== Custom Darkness Examples ===")
    for percent in [0, 25, 50, 75, 100]:
        mx11_val = darkness_to_mx11(percent)
        print(f"{percent:3}%: MX11 value {mx11_val}")
