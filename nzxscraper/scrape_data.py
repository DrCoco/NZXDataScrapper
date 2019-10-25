"""
All functions related to scraping company data from the NZX.
"""
import pandas
from datetime import datetime, timedelta
from numpy import loadtxt
import csv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from nzxscraper.environment import *
from nzxscraper.classes import Stock
from bs4 import BeautifulSoup
from time import sleep
from nzxscraper import logger, printProgressBar
import unicodedata
import warnings

def get_browser() :
    """
    Creates a chrome driver which will be used by selenium to conduct the website navigation
    Sets the following options to aid in webscraping
        - Auto file download
        - Removal the images
        - Disables internal pdf viewer

    Returns:
        webdriver: Driver for site navigation
    """
    # Set up driver options
    chromeOptions = Options()
    chromeOptions.add_argument('log-level=3') # Remove warnings
    chromeOptions.add_argument('--disable-gpu')
    chromeOptions.add_argument('headless')
    chromeOptions.add_argument("--proxy-server='direct://'")
    chromeOptions.add_argument("--proxy-bypass-list=*")
    chromeOptions.add_argument('--no-proxy-server')
    prefs = {"download.default_directory": downloadDirectory , # Sets default directory for downloads
            "directory_upgrade": True, # Provides write permissions to the directory
			"plugins.always_open_pdf_externally": True, # Disables the built-in pdf viewer (Helps with pdf download)
            "safebrowsing.enabled": True, # Tells  driver all file downloads and sites are safe
            "download.prompt_for_download": False, # Auto downloads files into default directory
            "profile.managed_default_content_settings.images":2 } # Removes images for faster load times
    chromeOptions.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(chromeDriverLocation, chrome_options = chromeOptions) # Apply options
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': downloadDirectory}}
    browser.execute("send_command", params)
    homeURL = "https://library.aut.ac.nz/databases/nzx-deep-archive"

    browser.get(homeURL)

    delay = 15 # seconds
    # Wait 15 seconds for the driver to get started and get to the landing page
    try:
        myElem = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, "form-field")))
        logger.info("Browser is ready!")
    except TimeoutException:
        logger.error("Loading took too much time!")
    logger.info("get_browser() complete")
    print("Chromium open")
    return browser

def get_stock_summary(stockSoup) :
    """
    Gets the stock summary information from the company summary page including Name, Price<br>, Market Cap, Price Earnings Ratio, Price Change, Ticker, Earnings per Share, Net Tangible Assets, Net DPS, Gross DPS, Beta Value, Price/NTA, Net Yield, Gross Yield, Sharpe Ratio

    Args:
        stockSoup (BeautifulSoup): The parsed page source of the summary page

    Returns:
        summaryDict (Dict): A dictionary which contains all the information captured on this page
    """

    summaryDict = {}
    summaryDict["Name"] = (stockSoup.find('h1').text).split(' -')[0]
    summaryDict["Price"] = float(stockSoup.find('td', text= 'Market Price').find_next_sibling('td').text.split('$')[1])
    summaryDict["Market Cap"] = float(stockSoup.find('td', text= 'Marketcap').find_next_sibling('td').text.split('$')[1].replace(',',''))
    try:
        summaryDict["Price Change"] = float(stockSoup.find('td', text= 'Price Change').find_next('td').text.split('$')[1])
    except IndexError:
        summaryDict["Price Change"] = float(0)
    summaryDict["Ticker"] = stockSoup.find('td', text= 'Ticker').find_next_sibling('td').text


    logger.debug(summaryDict)
    return summaryDict

def create_historical_prices_csv_link(stockTicker) :
    """
    Creates a csv link used to download the historical prices csv. Using todays date, and 3 years prior

    Args:
        stockTicker (String): Contains the ticker of the company

    Returns:
        csvLink (String): url which holds the csv
    """
    fromDate = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
    toDate = datetime.now().strftime('%Y-%m-%d')
    csvLink =  "https://companyresearch-nzx-com.ezproxy.aut.ac.nz/deep_ar/functions/csv_prices.php?"
    csvLink += ("default=" + stockTicker + "&" + "fd=" + fromDate + "&" + "td=" + toDate)
    logger.info("Pulling historical price data from: " + csvLink)
    return csvLink

def create_historical_dividends_csv_link(stockTicker) :
    """
    Creates a csv link used to download the historical dividends csv. Using todays date, and 3 years prior

    Args:
        stockTicker (String): Contains the ticker of the company

    Returns:
        csvLink (String): url which holds the csv
    """
    csvLink = "https://companyresearch-nzx-com.ezproxy.aut.ac.nz/deep_ar/divhistory_csv.php?selection=" + stockTicker
    logger.info("Pulling historical dividend data from: " + csvLink)
    return csvLink

def get_stock_historical_prices(stockHistoricalPricesCSV) :
    """
    Reads in the csv and outputs a dictionary for storage in the Stock class

    Args:
        stockHistoricalPricesCSV (String): Location where file is located

    Returns:
        (Dict): dictionary of historical prices
    """
    with warnings.catch_warnings():
        warnings.simplefilter(action='ignore', category=FutureWarning)
        prices = pandas.read_csv(stockHistoricalPricesCSV).to_dict('r')
        pricesReturn = []
        logger.debug(prices)
        for price in prices:
            price['Dollar Value Traded'] = price.pop('$ Value Traded')
            pricesReturn.append(price)
        return pricesReturn

def get_director_information(directorSoup):
    """
    Creates a dictionary containing names of all company directors

    Args:
        directorSoup (BeautifulSoup): Company directory page source

    Returns:
        directorDict (Dict): dictionary of company directors
    """
    tableData = directorSoup.find_all('table')[13]
    directorDict = {}
    directorTableData = [[ td.text for td in row.select('td')]
                         for row in tableData.find_all('tr')]
    for item in directorTableData:
        directorDict[unicodedata.normalize("NFKD", item[0]).replace('  ','')] = item[1]

    return directorDict

def get_stock_historical_dividends(stockHistoricalDividendsCSV) :
    """
    Reads in the csv and outputs a dictionary for storage in the Stock class

    Args:
        stockHistoricalDividendsCSV (String): Location where file is located

    Returns:
        (Dict): dictionary of historical dividends
    """
    with warnings.catch_warnings():
        warnings.simplefilter(action='ignore', category=FutureWarning)
        logger.debug(pandas.read_csv(stockHistoricalDividendsCSV))
        dividendDF = pandas.read_csv(stockHistoricalDividendsCSV)
        dividendDF = dividendDF.dropna()
        try:
            dividendDF = dividendDF[['Ex Date', 'Gross Amount']]
            dividendDF.columns = ['Date', 'Dividend Paid']
            dividendDF = dividendDF[dividendDF['Dividend Paid'] != '-']
            return dividendDF.to_dict('r')
        except:
            logger.warning("No dividend information")
            return None

def get_financial_profile(stockSoup) :
    """
    Creates a dictionary containing all the financial statement information of a company

    Args:
        stockSoup (BeautifulSoup): Financial Profile page source

    Returns:
        financialProfileDict (Dict): dictionary of company directors
    """
    tables = stockSoup.find_all('table')
    incomeTableHeaders = [item.get_text()[1:-1] for item in tables[7].find_all('tr')]
    incomeTableData =    [[ td.text for td in row.select('td')]
                        for row in tables[8].find_all('tr')]

    balanceTableHeaders = [item.get_text() for item in tables[11].find_all('td')]
    balanceTableData = [[ td.text for td in row.select('td')]
                        for row in tables[12].find_all('tr')]

    cashTableHeaders = [item.get_text() for item in tables[15].find_all('td')]
    cashTableData = [[ td.text for td in row.select('td')]
                        for row in tables[16].find_all('tr')]

    financialProfileDict =  {
                                'Data':
                                {
                                    'Income':{},
                                    'Balance':{},
                                    'Cash':{}
                                }
                            }

    for item in incomeTableHeaders:
        try:
            financialProfileDict['Data']['Income'][item] = float(incomeTableData[incomeTableHeaders.index(item)][0].replace(',',''))
        except:
            financialProfileDict['Data']['Income'][item] = incomeTableData[incomeTableHeaders.index(item)][0]

    for item in balanceTableHeaders:
        try:
            financialProfileDict['Data']['Balance'][item] = float(balanceTableData[balanceTableHeaders.index(item)][0].replace(',',''))
        except:
            financialProfileDict['Data']['Balance'][item] = balanceTableData[balanceTableHeaders.index(item)][0]

    for item in cashTableHeaders:
        try:
            financialProfileDict['Data']['Cash'][item] = float(cashTableData[cashTableHeaders.index(item)][0].replace(',',''))
        except:
            financialProfileDict['Data']['Cash'][item] = cashTableData[cashTableHeaders.index(item)][0]

    financialProfileDict['Year'] = financialProfileDict['Data']['Cash']['Period\xa0Ending'][-4:]

    return financialProfileDict

def get_company_profile(profileSoup):
    """
    Creates a dictionary containing names of all company profile information such as outlook, performance, and description

    Args:
        profileSoup (BeautifulSoup): Company Profile page source

    Returns:
        companyProfileDict (Dict): dictionary of company profile
    """
    companyProfileDict = {}
    # Put all table rows into a list.
    profList = profileSoup.find_all("tr", 'heading')

    #profList[1] is the business description header. Store business description in Dictionary
    companyProfileDict[profList[1].text] = profList[1].find_next_sibling('tr').td.text 
    #profList[2] is the overview header. Store in Dictionary
    companyProfileDict[profList[2].text] = profList[2].find_next_sibling('tr').td.text
    #profList[3] is the Performance header. Store in Dictionary
    companyProfileDict[profList[3].text] = profList[3].find_next_sibling('tr').td.text
    #profList[4] is the Outlook header. Store in Dictionary
    companyProfileDict[profList[4].text] = profList[4].find_next_sibling('tr').td.text
    return companyProfileDict

def list_companies(browser):
    """
    Creates a list which will be used to iterate through selected companies

    Args:
        browser (Selenium.WebDriver): The automated Chrome browser

    Returns:
        stockNames (List): list of company tickers to be scraped
    """
    # Login
    browser.find_element_by_xpath('//*[@id="username"]').send_keys(username)
    browser.find_element_by_xpath('//*[@id="password"]').send_keys(password)
    browser.find_element_by_xpath('//*[@id="login"]/section[4]/button').click()
    logger.info("Logged into NZX System")

    # Arrive at Market Activity Page
    browser.find_element_by_xpath(".//a[contains(text(), 'Company Research')]").click()
    logger.info("Arrived at Market Activity Page")
    # Click "View all" for main market
    browser.find_elements_by_xpath(".//a[contains(text(), 'view all')]")[0].click()
    logger.info("Arrived at Market Overview Page")
    # Sort in descending order by clicking the 26th "a" tag
    browser.find_elements_by_css_selector('td > a')[25].click()
    logger.info("Arrived at Market Overview sorted by marketcap in descending order")

    # Parse the page source into BeautifulSoup
    # The page is the list of stocks in Descending order of Market Cap
    html = browser.page_source
    htmlSoup =   BeautifulSoup(html,'lxml')
    logger.info("Market Overview Page parsed")

    # Put all the stock tickers into a list
    stocksSoup = htmlSoup.find_all('a', {'class' : 'text'}, limit=COMPANIES)
    stockNames = []
    for stock in stocksSoup :
        stockNames.append(stock.getText())

    logger.info("List of companies to scrape finalised")
    print("List of companies to scrape finalised")
    return stockNames

def scrape_company(browser, stock):
    """
    Contains the logic behind the scraping of an entire company's data

    Navigating to pages, downloading files

    Args:
        browser (Selenium.WebDriver): The automated Chrome browser
        stock (String): The stock ticker currently being scraped

    Returns:
        stockData (Stock): Class containing dictionaries of data
    """
    logger.info("Current Stock: " + stock)
    stockInnerIteration = 0
    numFuncs = 10
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))

    # Arrive at Summary & Ratios page and pull information
    browser.find_element_by_link_text(stock).click()
    summarySoup = BeautifulSoup(browser.page_source, 'lxml')
    logger.info("Pulling ratio information")
    stockSummaryDict = get_stock_summary(summarySoup)
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))
    stockRatioDict = get_ratios(summarySoup)
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))

    # Create csv link for historical prices and pull it into a temporary folder
    csvLink = create_historical_prices_csv_link(stock)
    logger.info("Pulling historical prices information")
    browser.get(csvLink)

    # Create csv link for dividends and pull it into a temporary folder
    csvLink = create_historical_dividends_csv_link(stock)
    logger.info("Pulling historical dividends information")
    browser.get(csvLink)

    # Arrive at Annual Reports and pull latest annual report
    # TODO May require refactor of xpath to shorten it (Looks nicer)
    # TODO change dl directory outside temp
    # Create try catch block
    try :
        logger.info("Pulling annual report")
        year = int(datetime.now().strftime('%Y'))
        annualReportLink = create_annual_report_link(stock, str(year))
        browser.get(annualReportLink)
        if browser.find_element_by_xpath(".//title[contains(text(), '404 Not Found')]"):
            browser.execute_script("window.history.go(-1)") # Go back to summary page
            annualReportLink = create_annual_report_link(stock, str(year-1))
            browser.get(annualReportLink)
            if browser.find_element_by_xpath(".//title[contains(text(), '404 Not Found')]"):
                browser.execute_script("window.history.go(-1)") # Go back to summary page
    except:
        pass
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))
    # browser.execute_script("window.history.go(-1)") # Go back to summary page

    # Create and get the tear sheet for the company
    tearSheetLink = 'https://companyresearch-nzx-com.ezproxy.aut.ac.nz/tearsheets/' + stock + '.pdf'
    browser.get(tearSheetLink)
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))

    # Arrive at Company Directory and pull directors information
    browser.find_element_by_xpath(".//span[contains(text(), 'Company Directory')]").click()
    directorSoup = BeautifulSoup(browser.page_source, 'lxml')
    logger.info("Pulling Director's information")
    stockDirectorDict = get_director_information(directorSoup)
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))
    browser.execute_script("window.history.go(-1)") # Go back to summary page

    # Arrive at Company Profile and pull description information
    browser.find_element_by_xpath(".//span[contains(text(), 'Company Profile')]").click()
    profileSoup = BeautifulSoup(browser.page_source, 'lxml')
    logger.info("Pulling company description")
    stockProfileDict = get_company_profile(profileSoup)
    logger.debug(stockProfileDict)
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))
    browser.execute_script("window.history.go(-1)") # Go back to summary page

    # Arrive at Financial Profile and pull debt-equity information
    browser.find_element_by_xpath(".//span[contains(text(), 'Financial Profile')]").click()
    stockSoup = BeautifulSoup(browser.page_source, 'lxml')
    logger.info("Pulling financial profile information")
    stockFinancialProfileDict = get_financial_profile(stockSoup)
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))
    browser.execute_script("window.history.go(-1)") # Go back to summary page

    # Read in the pries csv
    stockHistoricalPricesDict = get_stock_historical_prices(
                                tempDirectory + stock
                                + " Historical Prices.csv")
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))

    # Read in dividends csv
    stockHistoricalDividendsDict = get_stock_historical_dividends(
                                   tempDirectory + stock
                                   + " Historical Dividends.csv")
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))

    # Go back to the stock ticker page
    logger.info("Back to company listings")
    browser.execute_script("window.history.go(-1)")
    stockInnerIteration +=1
    printProgressBar(stockInnerIteration, numFuncs, prefix='Scraping {} data'.format(stock), suffix = 'of {} completed'.format(stock))

    # Create the stock obj and store it in an array
    stockData = {'Summary':stockSummaryDict,
                 'Ratio':stockRatioDict,
                 'HistoricalPrices':stockHistoricalPricesDict,
                 'HistoricalDividends':stockHistoricalDividendsDict,
                 'FinancialProfile':stockFinancialProfileDict,
                 'Profile':stockProfileDict,
                 'Directors':stockDirectorDict}

    return stockData

def get_ratios(stockSoup):
    """
    Scrapes the neccesary ratios from the summary page

    Args:
        stockSoup (BeautifulSoup): Company Summary page source

    Returns:
        ratioDict (Dictionary): A dictionary with all ratio data
    """
    ratioDict = {}

    try:
        ratioDict["Price Earnings Ratio"] = float(stockSoup.find('td', text= 'P/E ratio').find_next_sibling('td').text)
    except:
        ratioDict["Price Earnings Ratio"] = float(0)

    try:
        ratioDict["EPS"] = float(stockSoup.find('td', text= 'EPS').find_next('td').text.split('$')[1])
    except:
        ratioDict["EPS"] = float(0)

    try:
        ratioDict["NTA"] = float(stockSoup.find('td', text= 'NTA').find_next_sibling('td').text.split('$')[1])
    except:
        ratioDict["NTA"] = float(0)

    try:
        ratioDict["Net DPS"] = float(stockSoup.find('td', text= 'Net DPS').find_next_sibling('td').text.split('$')[1])
        ratioDict["Gross DPS"] = float(stockSoup.find('td', text= 'Gross DPS').find_next_sibling('td').text.split('$')[1])
    except:
        ratioDict['Net DPS'] = float(0)
        ratioDict["Gross DPS"] = float(0)

    try:
        ratioDict["Beta Value"] = float(stockSoup.find('td', text= 'Beta Value').find_next_sibling('td').text)
    except:
        ratioDict["Beta Value"] = float(0)

    try:
        ratioDict["Price/NTA"] = float(stockSoup.find('td', text= 'Price/NTA').find_next_sibling('td').text)
    except:
        ratioDict["Price/NTA"] = float(0)

    try:
        ratioDict["Net Yield"] = float(stockSoup.find('td', text= 'Net Yield').find_next_sibling('td').text)
        ratioDict["Gross Yield"] = float(stockSoup.find('td', text= 'Gross Yield').find_next_sibling('td').text)
    except ValueError:
        ratioDict["Net Yield"] = float(0)
        ratioDict["Gross Yield"] = float(0)

    try:
        ratioDict["Sharpe Ratio"] = float(stockSoup.find('td', text= 'Sharpe Ratio').find_next_sibling('td').text)
    except:
        ratioDict["Sharpe Ratio"] = float(0)

    return ratioDict

def create_annual_report_link(stock, year):
    """
    Creates a url to retrieve the annual report based on the current stock and year

    Args:
        year (String): the annual report release year
        stock (String): The stock ticker currently being scraped

    Returns:
        annualReportLink (String): url at which the annual report file is stored
    """

# 'https://companyresearch-nzx-com.ezproxy.aut.ac.nz/reports/nz/'2019/ANZ2019.pdf
    annualReportLink = 'https://companyresearch-nzx-com.ezproxy.aut.ac.nz/reports/nz/'
    annualReportLink += year + "/"
    annualReportLink += stock + year + ".pdf"

    return annualReportLink