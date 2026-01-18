import sys
import os

print(f"Python executable: {sys.executable}")

try:
    print("1. Importing marker components...")
    from marker.models import create_model_dict
    from marker.converters.pdf import PdfConverter
    from marker.config.parser import ConfigParser
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

try:
    print("2. Checking dependency versions...")
    import PIL
    import numpy
    print(f"Pillow version: {PIL.__version__}")
    print(f"Numpy version: {numpy.__version__}")
except ImportError as e:
    print(f"⚠️ Dependency missing: {e}")

try:
    print("3. Loading Marker models (this may take time)...")
    os.environ["INFERENCE_RAM"] = "4"
    os.environ["VRAM_PER_TASK"] = "3"
    
    model_dict = create_model_dict()
    print("✅ Models loaded successfully")
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    sys.exit(1)

print("🎉 Environment verification passed!")
