# tests/conftest.py

import sys
import os

from dotenv import load_dotenv, find_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_ = load_dotenv(find_dotenv())