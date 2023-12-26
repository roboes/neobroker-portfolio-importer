## Neobroker Portfolio Importer
# Last update: 2023-12-26


"""About: Web-scraping tool to extract and export current portfolio asset information from Scalable Capital and Trade Republic using Selenium library in Python."""


###############
# Initial Setup
###############

# Erase all declared global variables
globals().clear()


# Import packages
import os
from io import StringIO
import re
import time

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# Set working directory
# os.chdir(path=os.path.join(os.path.expanduser('~'), 'Downloads'))


###########
# Functions
###########


def selenium_webdriver():
    # WebDriver options
    webdriver_options = webdriver.ChromeOptions()
    webdriver_options.page_load_strategy = 'normal'
    webdriver_options.add_experimental_option(
        'prefs',
        {
            'enable_do_not_track': True,
            # 'download.default_directory': os.path.join(os.path.expanduser('~'), 'Downloads'),
            'download.prompt_for_download': False,
            'profile.default_content_setting_values.automatic_downloads': True,
        },
    )

    # if sys.platform in {'linux', 'linux2'}:
    #     webdriver_options.add_argument('--headless=new')
    #     webdriver_options.add_argument('--disable-dev-shm-usage')
    #     webdriver_options.add_argument('--no-sandbox')
    #     webdriver_options.add_argument('window-size=1400,900')
    #     webdriver_options.add_argument('--start-maximized')

    driver = webdriver.Chrome(
        service=Service(executable_path=ChromeDriverManager().install()),
        options=webdriver_options,
    )

    # Return objects
    return driver


def scalable_capital_portfolio_import(
    *,
    login=None,
    password=None,
    file_type='.xlsx',
    output_path=None,
):
    # Load Selenium WebDriver
    if 'driver' in vars():
        if driver.service.is_connectable() is True:
            pass

    else:
        driver = selenium_webdriver()

    # Open website
    driver.get(url='https://de.scalable.capital/en/secure-login')

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
                driver.find_element(
                    by=By.XPATH,
                    value='.//div[@data-testid="greeting-text"]',
                )
                break

            except NoSuchElementException:
                time.sleep(2)

    # Cookies: Only essentials
    try:
        driver.execute_script(
            script='''return document.querySelector("#usercentrics-root").shadowRoot.querySelector("button[data-testid='uc-deny-all-button']")''',
        ).click()

    except Exception:
        pass

    # Open broker
    driver.get(url='https://de.scalable.capital/broker/')
    time.sleep(5)

    # Import portfolio
    assets = (
        pd.read_html(io=StringIO(driver.page_source), flavor='lxml', encoding='utf-8')[
            0
        ]
        .rename(columns={'PortfolioSorting A-ZCreate group': 'name'})
        .assign(current_value=lambda row: row['name'])
        # name
        .assign(
            name=lambda row: row['name'].replace(
                to_replace=r'(^.*)(\u20ac.*)',
                value=r'\1',
                regex=True,
            ),
        )
        .assign(
            name=lambda row: row['name'].replace(
                to_replace=r'\u00ae',
                value=r'',
                regex=True,
            ),
        )
        # shares
        .assign(shares='')
        # current_value
        .assign(
            current_value=lambda row: row['current_value'].replace(
                to_replace=r'(^.*\u20ac)([0-9]+,[0-9]+\.[0-9]+|[0-9]+\.[0-9]+)(.*)?',
                value=r'\2',
                regex=True,
            ),
        )
        .assign(
            current_value=lambda row: row['current_value'].replace(
                to_replace=r',',
                value=r'',
                regex=True,
            ),
        )
        # .astype(dtype={'current_value': 'float'})
        .filter(items=['name', 'shares', 'current_value'])
    )

    # Get ISIN
    portfolio_list = driver.find_elements(
        by=By.XPATH,
        value='//div[@class="MuiTableContainer-root"]//tbody[@class="MuiTableBody-root"]//tr[starts-with(@class, "MuiTableRow-root jss")]',
    )

    data = []

    for portfolio in portfolio_list:
        d = {}

        # name
        d['name'] = portfolio.find_element(by=By.XPATH, value='.//span[@class]').text
        d['name'] = re.sub(pattern=r'\u00ae', repl=r'', string=d['name'], flags=0)

        # isin
        d['isin'] = portfolio.find_element(by=By.XPATH, value='.//img').get_attribute(
            'src',
        )
        d['isin'] = re.sub(
            pattern=r'(^.*\/performance\/)([A-Z]{2}[a-zA-Z0-9_]{10})(\/.*)',
            repl=r'\2',
            string=d['isin'],
            flags=0,
        )

        data.append(d)

    # Create DataFrame
    stocks_isin = pd.DataFrame(data=data, index=None, dtype=None)

    # Left join 'assets' with 'stocks_isin'
    assets = assets.merge(
        right=stocks_isin.drop_duplicates(
            subset=None,
            keep='first',
            ignore_index=True,
        ),
        how='left',
        on=['name'],
        indicator=False,
    )

    # Metadata
    assets = (
        assets.assign(date=pd.Timestamp.now().date())
        .assign(type='Investments')
        .assign(financial_institution='Scalable Capital')
        .filter(
            items=[
                'date',
                'type',
                'financial_institution',
                'name',
                'isin',
                'shares',
                'current_value',
            ],
        )
        .sort_values(by=['date', 'financial_institution', 'isin'], ignore_index=True)
    )

    # Delete objects
    del stocks_isin

    # Save
    if file_type == '.xlsx' and output_path is not None:
        with pd.ExcelWriter(
            path=output_path,
            date_format='YYYY-MM-DD',
            datetime_format='YYYY-MM-DD HH:MM:SS',
            engine='xlsxwriter',
            engine_kwargs={
                'options': {'strings_to_formulas': False, 'strings_to_urls': False},
            },
        ) as writer:
            assets.to_excel(
                excel_writer=writer,
                sheet_name='Portfolio',
                na_rep='',
                header=True,
                index=False,
                index_label=None,
                freeze_panes=(1, 0),
            )

    elif file_type == '.csv' and output_path is not None:
        assets.to_csv(
            path_or_buf=output_path,
            sep=',',
            na_rep='',
            header=True,
            index=False,
            index_label=None,
            encoding='utf-8',
        )

    else:
        assets.to_clipboard(excel=True, sep=None, index=False)

    # Return objects
    return assets


def trade_republic_portfolio_import(
    *,
    login=None,
    password=None,
    file_type='.xlsx',
    output_path=None,
):
    # Load Selenium WebDriver
    if 'driver' in vars():
        if driver.service.is_connectable() is True:
            pass

    else:
        driver = selenium_webdriver()

    # Open website
    driver.get(url='https://app.traderepublic.com')

    # Cookies: Accept Selected
    driver.find_element(
        by=By.XPATH,
        value='.//form[@class="consentCard__form"]//span[@class="buttonBase__title"]',
    ).click()

    # Login
    if login is not None and password is not None:
        # Login
        driver.find_element(by=By.ID, value='loginPhoneNumber__input').send_keys(login)
        time.sleep(1)
        driver.find_element(
            by=By.XPATH,
            value='.//span[@class="buttonBase__titleWrapper"]',
        ).click()

        # Password
        pins_input = driver.find_elements(
            by=By.XPATH,
            value='.//input[@type="password"]',
        )
        pins = list(password)

        for pin_input, pin in zip(pins_input, pins):
            pin_input.send_keys(int(pin))

    else:
        pass

    while True:
        try:
            driver.find_element(
                by=By.XPATH,
                value='.//span[@class="portfolio__pageTitle"]',
            )
            break

        except NoSuchElementException:
            time.sleep(2)

    # Open broker
    driver.get(url='https://app.traderepublic.com/portfolio')
    time.sleep(5)

    # Change view
    driver.find_element(by=By.XPATH, value='//div[@class="dropdownList"]').click()
    driver.find_element(
        by=By.XPATH,
        value='//div[@class="dropdownList"]//li[@id="investments-sinceBuyabs"]',
    ).click()

    # Import portfolio
    portfolio_list = driver.find_elements(
        by=By.XPATH,
        value='//ul[@class="portfolioInstrumentList"]//li',
    )

    data = []

    for portfolio in portfolio_list:
        d = {}

        # name
        d['name'] = portfolio.find_element(
            by=By.XPATH,
            value='.//span[@class="instrumentListItem__name"]',
        ).text

        # isin
        d['isin'] = portfolio.get_attribute('id')

        # shares
        d['shares'] = portfolio.find_element(
            by=By.XPATH,
            value='.//span[@class="instrumentListItem__priceRow"]//span',
        ).text

        # current_value
        d['current_value'] = portfolio.find_element(
            by=By.XPATH,
            value='.//span[@class="instrumentListItem__priceRow"]//span[@class="instrumentListItem__currentPrice"]',
        ).text
        d['current_value'] = re.sub(
            pattern=r' \u20ac',
            repl=r'',
            string=d['current_value'],
            flags=0,
        )
        d['current_value'] = float(d['current_value'])

        data.append(d)

    # Create DataFrame
    assets = pd.DataFrame(data=data, index=None, dtype=None).filter(
        items=['name', 'isin', 'shares', 'current_value'],
    )

    # Metadata
    assets = (
        assets.assign(date=pd.Timestamp.now().date())
        .assign(type='Investments')
        .assign(financial_institution='Trade Republic')
        .filter(
            items=[
                'date',
                'type',
                'financial_institution',
                'name',
                'isin',
                'shares',
                'current_value',
            ],
        )
        .sort_values(by=['date', 'financial_institution', 'isin'], ignore_index=True)
    )

    # Save
    if file_type == '.xlsx' and output_path is not None:
        with pd.ExcelWriter(
            path=output_path,
            date_format='YYYY-MM-DD',
            datetime_format='YYYY-MM-DD HH:MM:SS',
            engine='xlsxwriter',
            engine_kwargs={
                'options': {'strings_to_formulas': False, 'strings_to_urls': False},
            },
        ) as writer:
            assets.to_excel(
                excel_writer=writer,
                sheet_name='Portfolio',
                na_rep='',
                header=True,
                index=False,
                index_label=None,
                freeze_panes=(1, 0),
            )

    elif file_type == '.csv' and output_path is not None:
        assets.to_csv(
            path_or_buf=output_path,
            sep=',',
            na_rep='',
            header=True,
            index=False,
            index_label=None,
            encoding='utf-8',
        )

    else:
        assets.to_clipboard(excel=True, sep=None, index=False)

    # Return objects
    return assets


##############################
# Neobroker Portfolio Importer
##############################

scalable_capital_portfolio_import(
    login=None,
    password=None,
    file_type='.xlsx',
    output_path=os.path.join(
        os.path.expanduser('~'),
        'Downloads',
        'Assets Scalable Capital.xlsx',
    ),
)

trade_republic_portfolio_import(
    login=None,
    password=None,
    file_type='.xlsx',
    output_path=os.path.join(
        os.path.expanduser('~'),
        'Downloads',
        'Assets Trade Republic.xlsx',
    ),
)

# Quit WebDriver
if 'driver' in vars():
    driver.quit()
