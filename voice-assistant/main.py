"""Main application entry point for Speechy - Your AI Voice Assistant."""

import sys
# Force early numpy import to prevent PyInstaller bundling issues
import numpy as np
from application_manager import main

if __name__ == "__main__":
    sys.exit(main())