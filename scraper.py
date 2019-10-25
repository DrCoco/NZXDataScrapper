from bs4 import BeautifulSoup
import sys
from time import time
from nzxscraper.scrape_data import get_browser, list_companies, scrape_company
from nzxscraper.save_data import save_data, save_log_to_pastebin
from nzxscraper.environment import DEBUG, downloadDirectory, COMPANIES
import shutil
from nzxscraper import logger, printProgressBar
from nzxscraper.analyse import analyse_company_risk, score_companies

def start_scraping():
    # Log environment
    logger.info("Download directory: " + downloadDirectory)
    startTime = time()
    browser = get_browser()
    success = False

    try:
        stockTickersList = list_companies(browser)

        # Initialise the array which is  going to store Stock class objects
        stockDataArray = []

        # For each ticker in the list, find the link to the respective summary page
        stockIteration = 0
        printProgressBar(stockIteration, len(stockTickersList), prefix='Scraping company data', suffix = 'of companies completed', length=50)
        for stock in stockTickersList :
            stockData = scrape_company(browser, stock)
            stockDataArray.append(stockData)
            stockIteration += 1
            printProgressBar(stockIteration, len(stockTickersList), prefix='Scraping company data', suffix = 'of companies completed', length=50)
        success = True
        logger.info("Scraping complete")
        print("Scraping complete")
    finally:
        browser.quit()
        if success:
            analyse_company_risk(stockDataArray)
            score_companies(stockDataArray)
        save_data(stockDataArray, success)
        logger.info("Temporary files deleted")
        shutil.rmtree(downloadDirectory)

        endTime = time()
        logger.info("That took a total of: " + str(round(endTime-startTime)) + " seconds.")
        logger.info(str(round((endTime-startTime)/COMPANIES)) + " seconds per company.")
        logger.info("Scraping and saving complete")
        print("That took a total of: " + str(round(endTime-startTime)) + " seconds.")
        print(str(round((endTime-startTime)/COMPANIES)) + " seconds per company.")
        print("Scraping and saving complete")
        # Pastebin logs are currently disabled as feature is not working as intended
        # save_log_to_pastebin()

if __name__ == "__main__":
    start_scraping()
