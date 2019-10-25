"""
All contained classes are now DEPRECATED.
"""
class Stock:
    """
        This class is now DEPRECATED, we now use a dictionary to store the neccesary company information.
        See scrape_data(419)
    """
    def __init__(self, stockSummaryDict, stockHistoricalPricesDict, stockHistoricalDividendsDict, stockFinancialProfileDict, stockCompanyProfileDict, stockDirectorDict) :
        self.stockSummaryDict = stockSummaryDict
        self.stockHistoricalPricesDict = stockHistoricalPricesDict
        self.stockHistoricalDividendsDict = stockHistoricalDividendsDict
        self.stockFinancialProfileDict = stockFinancialProfileDict
        self.stockCompanyProfileDict = stockCompanyProfileDict
        self.stockDirectorDict = stockDirectorDict

    def __str__(self):
        return str(self.__dict__)