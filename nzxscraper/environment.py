"""
Several variables containing OS and user specific data, as well as testing toggles.
"""
from pathlib import Path
import os
import platform
dirname = os.getcwd()

username = os.environ.get('USERNAME')
password = os.environ.get('PASSWORD')
DEBUG = os.environ.get('DEBUG')
COMPANIES = int(os.environ.get('COMPANIES'))

downloadDirectory = str(Path(os.path.join(dirname, 'temp')))
tempDirectory = str(Path(r"temp/a"))[:-1]
if platform.system() is "Windows":
    chromeDriverLocation = r"C:\Users\Kiran\Documents\GitHub\ScraperHeroku\chromedriver.exe"
else:
    chromeDriverLocation = "/app/.chromedriver/bin/chromedriver"
