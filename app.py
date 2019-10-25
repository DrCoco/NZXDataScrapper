from flask import Flask
from flask_restful import Api

from resources.run_scraper import Scraper

app = Flask(__name__)
api = Api(app)

api.add_resource(Scraper, "/scrape")

if __name__ == "__main__":
  app.run()