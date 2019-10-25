"""
    Contains all functions required to send data externally.
"""
from nzxscraper.environment import DEBUG, tempDirectory
from nzxscraper import logger, printProgressBar
from datetime import datetime
import requests
import json
import platform
from xml.etree import ElementTree
import os
import glob

def getDestinationURL():
    """
    Retrieve the destination URL based on the evironment the script is running in

    Returns:
        destinationURL (String): The URL that scraped data and files will be sent to
    """
    linodeURL = 'http://li555-251.members.linode.com/update'
    localTestURL = 'http://localhost:8000/update'
    return localTestURL if platform.system() == 'Windows' else linodeURL

def save_data(stockDataArray, success):
    """
    Constructs a dictionary of company information. Converts it JSON, and sends it externally using send_to_server()

    Args:
        stockDataArray (List): dictionary of all company information
        success (Boolean): To indicate whether the scraping was succesful, to identify if processing needs to occur
    """
    currentTimeStamp = datetime.now().strftime('%Y/%m/%d')
    scrapeInsert = {currentTimeStamp:{'Date':currentTimeStamp}}
    if success:
        logger.info("Saving data")
        print("Saving data")

        dividendInsert = {'Data':{}, 'Name': 'HistoricalDividends'}
        priceInsert = {'Data':{}, 'Name': 'HistoricalPrices'}

        stockIteration = 0
        # Select stock
        for stock in stockDataArray:
            currentStockTicker = stock['Summary']['Ticker']
            logger.info("Saving data for: " + currentStockTicker)
            stockInsert = {}

            # Create stock dict from scraped data
            for sectionKey, sectionData in stock.items():
                logger.info(sectionKey)
                sectionInsert = {}
                if sectionKey == 'HistoricalPrices':
                    for line in sectionData:
                        logger.debug(line)
                        dateString = line.pop('Date')
                        dateString = (datetime.strptime(dateString, '%d %b %Y')).strftime("%Y-%m-%d")
                        sectionInsert[dateString] = line
                    stockInsert[sectionKey] = sectionInsert
                elif sectionKey == 'HistoricalDividends':
                    try:
                        for line in sectionData:
                            logger.debug(line)
                            dateString = line.pop('Date')
                            dateString = (datetime.strptime(dateString, '%d %b %Y')).strftime("%Y-%m-%d")
                            sectionInsert[dateString] = line.pop('Dividend Paid')
                        stockInsert[sectionKey] = sectionInsert
                    except TypeError:
                        pass
                else:
                    for elementKey, elementValue in sectionData.items():
                        sectionInsert[elementKey] = elementValue
                    stockInsert[sectionKey] = sectionInsert

            scrapeInsert[currentTimeStamp][stock['Summary']['Ticker']] = stockInsert
            stockIteration += 1
            printProgressBar(stockIteration, len(stockDataArray), prefix='Saving {} data'.format(stock['Summary']['Ticker']), suffix = 'of {} companies completed'.format(len(stockDataArray)))

        with open('data.txt', 'w') as outfile:
            json.dump(scrapeInsert, outfile, indent=4)

        # save_result_to_pastebin(scrapeInsert, currentTimeStamp)
        send_to_server(scrapeInsert)
        send_files_to_server()
    else:
        scrapeInsert[currentTimeStamp] = {}
        # save_result_to_pastebin(scrapeInsert, currentTimeStamp)
        send_to_server(scrapeInsert)

def send_to_server(scrapeInsert):
    """
    Sends the given JSON object to the appropriate URL

    Args:
        scrapeInsert (JSON): JSON object with all company information
    """
    destinationURL = getDestinationURL()
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post(destinationURL, data=json.dumps(scrapeInsert), headers=headers)
    logger.info("Sent JSON data to {}".format(destinationURL))
    logger.info("Received response {}".format(r.status_code))

def save_log_to_pastebin():
    """
    This method is used to retrieve logs from Heroku, where it would otherwise be impossible
    It sends any log files to Pastebin, where we can monitor how it is functioning
    """
    pastebinApiURL = 'https://pastebin.com/api/api_post.php'
    dev_key = '5f996bee7fa49af7481927ddce874367'
    user_key = '77787566e1fa286ab849d7b0e22169c9'

    # Check number of pastes
    dataList = {}
    dataList['api_dev_key'] = dev_key
    dataList['api_option'] = 'list'
    dataList['api_user_key'] = user_key
    r = requests.post(pastebinApiURL, data=dataList)
    pastesString = "<pastes>" + r.text + "</pastes>"
    root = ElementTree.fromstring(pastesString)
    numPastes = len(root.findall('paste'))

    # Find the oldest paste then delete it
    if numPastes == 10:
        logger.info("10 Pastes found, deleting one to make paste for next one")
        oldestPaste = root[0][0].text
        oldestDate = int(root[0][1].text)
        for paste in root:
            if int(paste[1].text) < oldestDate:
                oldestPaste = paste[0].text
                oldestDate = int(paste[1].text)

        dataDelete = {}
        dataDelete['api_dev_key'] = dev_key
        dataDelete['api_option'] = 'delete'
        dataDelete['api_user_key'] = user_key
        dataDelete['api_paste_key'] = oldestPaste
        r = requests.post(pastebinApiURL,data=dataDelete)
        logger.info("Deleted {} paste".format(oldestPaste))

    logger.info("Sending logs to Pastebin")
    logger.info("Bye, Felicia")

    dataPaste = {}
    dataPaste['api_dev_key'] = dev_key
    dataPaste['api_option'] = 'paste'
    with open("python_logging.log", "r") as logging_file:
        dataPaste['api_paste_code'] = logging_file.read()
    dataPaste['api_user_key'] = user_key
    dataPaste['api_paste_name'] = 'JSON Scrape Backup ' + str(datetime.now())
    # dataPaste['api_paste_format'] = 'json'
    dataPaste['api_paste_private'] = '2'
    dataPaste['api_paste_expire_date'] = '6M'



    r = requests.post(pastebinApiURL,data=dataPaste)
    print("New Paste at: " + r.text)

def send_files_to_server():
    """
    This method is used to retrieve all pdf files from the temp folder and send them to the appropriate URL
    """
    fileList = os.listdir("temp")
    fileIteration = 0
    pdfIteration = 0
    destinationURL = getDestinationURL()
    logger.info("Sending files to: " + destinationURL)

    for file in fileList:
        fileIteration += 1
        fileJSON = {}
        if file.endswith(".pdf"):
            pdfIteration += 1
            with open(os.path.join(r'temp', file), 'rb') as fileContent:
                fileJSON[file] = fileContent
                r = requests.post(destinationURL, files=fileJSON)
            logger.info("Sent file: " + file)
            printProgressBar(fileIteration, len(fileList), prefix='Saving {} data'.format(file).ljust(24), suffix = '| {} files completed'.format(pdfIteration), length = 10)