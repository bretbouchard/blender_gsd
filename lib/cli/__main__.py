"""
Blender GSD CLI Entry Point

Allows running the CLI as a module:
    python -m lib.cli init my-project
    python -m lib.cli templates list
    python -m lib.cli validate .
    python -m lib.cli dashboard
"""

from .main import main
import sys

if __name__ == "__main__":
    sys.exit(main())
