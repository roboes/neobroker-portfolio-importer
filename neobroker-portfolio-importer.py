## Neobroker Portfolio Importer
# Last update: 2023-05-31


###############
# Initial Setup
###############

# Erase all declared global variables
globals().clear()


# Import packages
import os
import re
import time

# import lxml
# import openpyxl
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# Set working directory
os.chdir(path=os.path.join(os.path.expanduser('~'), 'Downloads'))




###########
# Functions
###########

# Selenium Webdriver
def selenium_webdriver():

    # Webdriver options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.page_load_strategy = 'normal'


    # Webdriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    # Return objects
    return driver



# Selenium webdriver quit
def selenium_webdriver_quit():

        # Import or create global variables
        global driver


        # Driver quit
        driver.quit()


        # Delete objects
        del driver



# Scalable Capital Portfolio Import
def scalable_capital_portfolio_import(*, login=None, password=None, transpose=False, path=os.path.join(os.path.expanduser('~'), 'Downloads'), file_type='.xlsx', file_name='Assets.xlsx'):

    # Import or create global variables
    global driver


    # Load Selenium webdriver
    if 'driver' in vars() or 'driver' in globals():
        if driver.service.is_connectable() == True:
            pass

    else:
        driver = selenium_webdriver()


    # Open website
    driver.get('https://de.scalable.capital/en/secure-login')

    # Cookies: Allow selection
    try:
        driver.find_element(by=By.ID, value='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection').click()

    except:
        pass


    # Login
    if login is not None and password is not None:

        # Login
        driver.find_element(by=By.ID, value='username').send_keys(login)
        driver.find_element(by=By.ID, value='password').send_keys(password)
        time.sleep(2)

        # Password
        driver.find_element(by=By.XPATH, value='.//*[@type="submit"]').submit()

    else:
        while True:

            try:
                driver.find_element(by=By.XPATH, value='.//div[@data-testid="greeting-text"]')
                break

            except NoSuchElementException:
                time.sleep(2)


    # Open broker
    driver.get('https://de.scalable.capital/broker/')
    time.sleep(5)


    # Import portfolio
    assets = (pd.read_html(io=driver.page_source, flavor='lxml', encoding='utf8')[0]
        .rename(columns={'PortfolioSorting A-ZCreate group': 'name'})
        .assign(current_value = lambda row: row['name'])

        # name
        .assign(name = lambda row: row['name'].str.replace(pat=r'(^.*)(\u20ac.*)', repl=r'\1', regex=True))
        .assign(name = lambda row: row['name'].str.replace(pat=r'\u00ae', repl=r'', regex=True))

        # current_value
        .assign(current_value = lambda row: row['current_value'].str.replace(pat=r'(^.*\u20ac)([0-9]+,[0-9]+\.[0-9]+|[0-9]+\.[0-9]+)(.*)?', repl=r'\2', regex=True))
        .assign(current_value = lambda row: row['current_value'].str.replace(pat=r',', repl=r'', regex=True))

        .astype(dtype={'current_value': 'float'})
        .filter(items=['name', 'current_value'])
    )


    # Get ISIN
    portfolio_list = driver.find_elements(by=By.XPATH, value='//div[@class="MuiTableContainer-root"]//tbody[@class="MuiTableBody-root"]//tr[starts-with(@class, "MuiTableRow-root jss")]')

    data = []

    for portfolio in portfolio_list:

        d = {}

        # name
        d['name'] = portfolio.find_element(by=By.XPATH, value='.//span[@class]').text
        d['name'] = re.sub(pattern=r'\u00ae', repl=r'', string=d['name'])

        # isin
        d['isin'] = portfolio.find_element(by=By.XPATH, value='.//img').get_attribute('src')
        d['isin'] = re.sub(pattern=r'(^.*\/performance\/)([A-Z]{2}[a-zA-Z0-9_]{10})(\/.*)', repl=r'\2', string=d['isin'])

        data.append(d)


    # Create DataFrame
    stocks_isin = pd.DataFrame(data=data, index=None, dtype=None)


    # Left join 'assets' with 'stocks_isin'
    assets = (assets
        .merge(stocks_isin.drop_duplicates(subset=None, keep='first', ignore_index=True), how='left', on=['name'], indicator=False)
        .filter(items=['name', 'isin', 'current_value'])
        .sort_values(by=['isin'], ignore_index=True)
    )


    # Delete objects
    del stocks_isin


    # Transpose
    if transpose is True:
        assets = (assets.set_index(keys='name', drop=True, append=False)
            .transpose())


    # Save
    if file_type == '.xlsx':
        assets.to_excel(excel_writer=os.path.join(path, file_name), sheet_name='Stocks', na_rep='', header=True, index=False, index_label=None, freeze_panes=(1, 0), engine='openpyxl')

    elif file_type == '.csv':
        assets.to_csv(path_or_buf=os.path.join(path, file_name), sep=',', na_rep='', header=True, index=False, index_label=None, encoding='utf8')

    else:
        assets.to_clipboard(excel=True, sep=None, index=False)


    # Return objects
    return assets



# Trade Republic Portfolio Import
def trade_republic_portfolio_import(*, login, password, transpose=False, path=os.path.join(os.path.expanduser('~'), 'Downloads'), file_type='.xlsx', file_name='Assets.xlsx'):

    # Import or create global variables
    global driver


    # Load Selenium webdriver
    if 'driver' in vars() or 'driver' in globals():
        if driver.service.is_connectable() == True:
            pass

    else:
        driver = selenium_webdriver()


    # Open website
    driver.get('https://app.traderepublic.com')

    # Cookies: Accept Selected
    driver.find_element(by=By.XPATH, value='.//form[@class="consentCard__form"]//span[@class="buttonBase__title"]').click()

    # Login
    if login is not None and password is not None:

        # Login
        driver.find_element(by=By.ID, value='loginPhoneNumber__input').send_keys(login)
        time.sleep(1)
        driver.find_element(by=By.XPATH, value='.//span[@class="buttonBase__titleWrapper"]').click()

        # Password
        pins_input = driver.find_elements(by=By.XPATH, value='.//input[@type="password"]')
        pins = list(password)

        for pin_input, pin in zip(pins_input, pins):
            pin_input.send_keys(int(pin))

    else:
        pass


    while True:

        try:
            driver.find_element(by=By.XPATH, value='.//span[@class="portfolio__pageTitle"]')
            break

        except NoSuchElementException:
            time.sleep(2)


    # Open broker
    driver.get('https://app.traderepublic.com/portfolio')
    time.sleep(5)


    # Import portfolio
    portfolio_list = driver.find_elements(by=By.XPATH, value='//ul[@class="portfolioInstrumentList"]//li')

    data = []

    for portfolio in portfolio_list:

        d = {}

        # name
        d['name'] = portfolio.find_element(by=By.XPATH, value='.//span[@class="instrumentListItem__name"]').text

        # isin
        d['isin'] = portfolio.get_attribute('id')

        # current_value
        d['current_value'] = portfolio.find_element(by=By.XPATH, value='.//span[@class="instrumentListItem__currentPrice"]').text
        d['current_value'] = re.sub(pattern=r' \u20ac', repl=r'', string=d['current_value'])
        d['current_value'] = float(d['current_value'])

        data.append(d)


    # Create DataFrame
    assets = (pd.DataFrame(data=data, index=None, dtype=None)
        .filter(items=['name', 'isin', 'current_value'])
        .sort_values(by=['isin'], ignore_index=True)
    )


    # Transpose
    if transpose is True:
        assets = (assets.set_index(keys='name', drop=True, append=False)
            .transpose())


    # Save
    if file_type == '.xlsx':
        assets.to_excel(excel_writer=os.path.join(path, file_name), sheet_name='Stocks', na_rep='', header=True, index=False, index_label=None, freeze_panes=(1, 0), engine='openpyxl')

    elif file_type == '.csv':
        assets.to_csv(path_or_buf=os.path.join(path, file_name), sep=',', na_rep='', header=True, index=False, index_label=None, encoding='utf8')

    else:
        assets.to_clipboard(excel=True, sep=None, index=False)


    # Return objects
    return assets




##############################
# Neobroker Portfolio Importer
##############################

scalable_capital_portfolio_import(login=None, password=None, transpose=False, file_type='.xlsx', file_name='Assets Scalable Capital.xlsx')

trade_republic_portfolio_import(login=None, password=None, transpose=False, file_type='.xlsx', file_name='Assets Trade Republic.xlsx')

selenium_webdriver_quit()
