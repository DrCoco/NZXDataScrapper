from flask_restful import Resource
import threading
import time
from scraper import start_scraping

class Scraper(Resource):
	def get(self):
		bg = threading.Thread(target=start_scraping)
		bg.start()
		return "You've started the scraping process", 200