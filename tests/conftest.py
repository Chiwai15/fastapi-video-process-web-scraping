import sys
import os
from pathlib import Path

# Get paths
project_root = Path(__file__).parent.parent
app_dir = project_root / 'app'

# Add paths to sys.path
sys.path.insert(0, str(project_root))
sys.path.insert(1, str(app_dir))
