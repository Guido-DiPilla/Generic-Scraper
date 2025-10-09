#!/usr/bin/env python3
"""
Launch the Client Generator GUI
Simple launcher script for the client generator tool.
"""

import sys
from pathlib import Path

# Add the current directory to path so we can import client_generator
sys.path.insert(0, str(Path(__file__).parent))

try:
    from client_generator import main
    
    if __name__ == "__main__":
        print("🚀 Launching Generic Scraper - Client Generator...")
        main()
        
except ImportError as e:
    print(f"❌ Error importing client generator: {e}")
    print("Make sure you're running this from the scraper directory.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error running client generator: {e}")
    sys.exit(1)