import os
from moviepy.config import change_settings

# Set the ImageMagick binary path
IMAGEMAGICK_BINARY = "/usr/bin/convert"  # Standard path in most Linux distributions

# Configure MoviePy to use the specified ImageMagick binary
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})

def check_imagemagick():
    """
    Verify that ImageMagick is properly installed and configured.
    Returns True if successful, False otherwise.
    """
    import subprocess
    try:
        # Check if ImageMagick's convert command is available
        result = subprocess.run([IMAGEMAGICK_BINARY, "--version"], 
                               capture_output=True, text=True)
        print(f"ImageMagick found: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"Error checking ImageMagick: {e}")
        return False

def check_font_availability(font_name="Poppins-Black"):
    """
    Check if a specific font is available to ImageMagick.
    """
    import subprocess
    try:
        # List fonts available to ImageMagick
        result = subprocess.run([IMAGEMAGICK_BINARY, "-list", "font"], 
                               capture_output=True, text=True)
        
        # Check if our font is in the list
        if font_name.lower() in result.stdout.lower():
            print(f"Font '{font_name}' is available to ImageMagick.")
            return True
        else:
            print(f"Font '{font_name}' not found in ImageMagick fonts.")
            print("Available fonts include:")
            # Show a sample of available fonts
            font_list = [line for line in result.stdout.split('\n') if 'font:' in line.lower()]
            for font in font_list[:10]:  # Show first 10 fonts
                print(f"  {font}")
            return False
    except Exception as e:
        print(f"Error checking font availability: {e}")
        return False