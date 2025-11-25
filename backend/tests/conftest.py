import sys
import os

# backend root
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

#  backend added to Python search path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
