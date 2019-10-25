"""
Contains functions related to the analysis of scraped data.
"""

from nzxscraper import logger, printProgressBar
import statistics

def find_normal_ranges(stockDataArray):
	"""
	Finds the max and min for each index. To prevent a company from receiving a perfect or 0 zero, a buffer of 1 has been added.

    Args:
        stockDataArray (List): dictionary of all company information

    Returns:
		Dict: Contains the max and min of each index
	"""
	normalisationRanges = {
							"Dividend Yield Max": 0,
							"Dividend Yield Min": 0,
							"Return on Equity Max": 0,
							"Return on Equity Min": 0,
							"Sharpe Ratio Max": 0,
							"Sharpe Ratio Min": 0,
							"Debt Equity Max": 0,
							"Debt Equity Min": 0,
							}
	for stock in stockDataArray:
		# Dividend Yield Ranges
		if stock['Ratio']['Net Yield'] >= normalisationRanges['Dividend Yield Max']:
			normalisationRanges['Dividend Yield Max'] = stock['Ratio']['Net Yield'] + 1
		if stock['Ratio']['Net Yield'] <= normalisationRanges['Dividend Yield Min']:
			normalisationRanges['Dividend Yield Min'] = stock['Ratio']['Net Yield'] - 1

		# Return on Equity Ranges
		netIncome = stock['FinancialProfile']['Data']['Income']['Net Income']
		shareholderEquity = stock['FinancialProfile']['Data']['Balance']['Total Equity']
		stock['Ratio']['Return on Equity'] = (netIncome / shareholderEquity) * 100

		if stock['Ratio']['Return on Equity'] >= normalisationRanges['Return on Equity Max']:
			normalisationRanges['Return on Equity Max'] = stock['Ratio']['Return on Equity'] + 1
		if stock['Ratio']['Return on Equity'] <= normalisationRanges['Return on Equity Min']:
			normalisationRanges['Return on Equity Min'] = stock['Ratio']['Return on Equity'] - 1

		# Sharpe Ratio
		if stock['Ratio']['Sharpe Ratio'] >= normalisationRanges['Sharpe Ratio Max']:
			normalisationRanges['Sharpe Ratio Max'] = stock['Ratio']['Sharpe Ratio'] + 1
		if stock['Ratio']['Sharpe Ratio'] <= normalisationRanges['Sharpe Ratio Min']:
			normalisationRanges['Sharpe Ratio Min'] = stock['Ratio']['Sharpe Ratio'] - 1

		# Debt Equity
		totalLiability = stock['FinancialProfile']['Data']['Balance']['Total Liabilities']
		totalEquity = stock['FinancialProfile']['Data']['Balance']['Total Equity']
		stock['Ratio']['Debt Equity'] = totalLiability/totalEquity

		if stock['Ratio']['Debt Equity'] >= normalisationRanges['Debt Equity Max']:
			normalisationRanges['Debt Equity Max'] = stock['Ratio']['Debt Equity'] + 1
		if stock['Ratio']['Debt Equity'] <= normalisationRanges['Debt Equity Min']:
			normalisationRanges['Debt Equity Min'] = stock['Ratio']['Debt Equity'] - 1
	logger.info(normalisationRanges)
	return normalisationRanges

def score_companies(stockDataArray):
	"""
    Scores each company based on their own values compared to other companies.
	For this, we are using the geometric average to get a more accurate represention.
    Args:
        stockDataArray (List): dictionary of all company information
    """

	normalisationRanges = find_normal_ranges(stockDataArray)

	for stock in stockDataArray:
		debtEquityIndexValue = findDebtEquityIndexValue(stock, normalisationRanges['Debt Equity Max'], normalisationRanges['Debt Equity Min'])
		netDividendYield = findNetDividendYield(stock, normalisationRanges['Dividend Yield Max'], normalisationRanges['Dividend Yield Min'])
		sharpeRatioIndexValue = findSharpeRatioIndexValue(stock, normalisationRanges['Sharpe Ratio Max'], normalisationRanges['Sharpe Ratio Min'])
		returnOnEquityIndexValue = findReturnOnEquityIndexValue(stock, normalisationRanges['Return on Equity Max'],  normalisationRanges['Return on Equity Min'])

		# Geometric average to make score more accurate
		score = (debtEquityIndexValue * sharpeRatioIndexValue * returnOnEquityIndexValue * netDividendYield ) ** 0.25
		stock['Summary']['Score'] = score
		logger.info("{} | Score: {}".format(stock['Summary']['Ticker'], score))
		print("{} got a score of: {}".format(stock['Summary']['Ticker'], score))

def findNetDividendYield(stock, max, min):
	"""
    Args:
        stock (Dict): dictionary of company information
        max (Float): the maximum dividend yield within this scrape + 1
        min (Float): the minimum dividend yield within this scrape 1

    Returns:
	    index (Float): The normalised value of the company's dividend yield (Always between 0 and 1)
    """
	netDividendYield = stock['Ratio']['Net Yield']
	index = (netDividendYield - min) / (max - min)
	stock['Summary']['Net Dividend Yield Index'] = index
	logger.info("{} | Yield: {}".format(stock['Summary']['Ticker'], index))
	return index

def  findReturnOnEquityIndexValue(stock, max, min):
	"""
    Args:
        stock (Dict): dictionary of company information
        max (Float): the maximum return on equity within this scrape + 1
        min (Float): the minimum return on equity within this scrape 1

    Returns:
	    index (Float): The normalised value of the company's return on equity (Always between 0 and 1)
    """
	stockRoE = stock['Ratio']['Return on Equity']
	index = (stockRoE - min) / (max - min)
	stock['Summary']['Return on Equity Index'] = index
	logger.info("{} | RoE Index: {}".format(stock['Summary']['Ticker'], index))
	return index

def findSharpeRatioIndexValue(stock, max, min):
	"""
    Args:
        stock (Dict): dictionary of company information
        max (Float): the maximum sharpe ratio within this scrape + 1
        min (Float): the minimum sharpe ratio within this scrape 1

    Returns:
	    index (Float): The normalised value of the company's sharpe ratio (Always between 0 and 1)
    """
	stockSharpeRatio = stock['Ratio']['Sharpe Ratio']
	index = (stockSharpeRatio - min) / (max - min)
	stock['Summary']['Sharpe Ratio Index'] = index
	logger.info("{} | Sharpe: {}".format(stock['Summary']['Ticker'],index))
	return index

def findDebtEquityIndexValue(stock, max, min):
	"""
    Args:
        stock (Dict): dictionary of company information
        max (Float): the maximum debt equity within this scrape + 1
        min (Float): the minimum debt equity within this scrape 1

    Returns:
	    index (Float): The normalised value of the company's debt equity (Always between 0 and 1)
    """
	stockDebtEquity = stock['Ratio']['Debt Equity']
	index = 1 - ((stockDebtEquity - min) / (max - min))
	stock['Summary']['Debt Equity Index'] = index
	logger.info("{} | Debt Equity: {}".format(stock['Summary']['Ticker'], index))
	return index

def analyse_company_risk(stockDataArray):
	"""
	For each company, creates a list of that company's stock price.
	The standard deviation of this list is used as an indicator for risk.
    Saves the calculate risk score into the Summary Dictionary.

    Args:
		stockDataArray (List): dictionary of all company information
	"""
	for stock in stockDataArray:
		priceData = stock['HistoricalPrices']
		priceList = []
		for price in priceData:
			priceList.append(price['Last'])
		risk = statistics.stdev(priceList)
		logger.info("{} | Risk: {}".format(stock['Summary']['Ticker'], risk))
		stock['Summary']['Risk'] = risk


