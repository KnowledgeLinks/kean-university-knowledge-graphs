"""Module run Flask Development Server"""
__author__ = "Jeremy Nelson"

import os
import sys
sys.path.append(os.path.abspath(os.path.curdir))
from concierge import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
