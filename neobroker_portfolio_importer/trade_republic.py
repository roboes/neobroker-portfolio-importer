"""About: Web-scraping tool to extract and export current portfolio asset information from Trade Republic using Selenium library in Python."""

# Import packages
import re
import time

import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from .selenium_utils import selenium_webdriver


# Settings

## Copy-on-Write (will be enabled by default in version 3.0)
if pd.__version__ >= '1.5.0' and pd.__version__ < '3.0.0':
    pd.options.mode.copy_on_write = True


# Functions
def trade_republic_portfolio_import(
    *,
    login=None,
    password=None,
    file_type='.xlsx',
    output_path=None,
    return_df=False,
):
    # Load Selenium WebDriver
    if 'driver' in vars():
        if driver.service.is_connectable() is True:
            pass

    else:
        driver = selenium_webdriver(web_browser='chrome', javascript_disable=True)

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

    # The portfolio calculation has been updated
    try:
        driver.find_element(
            by=By.XPATH,
            value='.//div[@class="focusManager__content"]//button',
        ).click()
        time.sleep(2)

    except Exception:
        pass

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

        # asset_name
        d['asset_name'] = portfolio.find_element(
            by=By.XPATH,
            value='.//span[@class="instrumentListItem__name"]',
        ).text

        # isin_code
        d['isin_code'] = portfolio.get_attribute(name='id')

        # shares
        d['shares'] = portfolio.find_element(
            by=By.XPATH,
            value='.//span[@class="instrumentListItem__priceRow"]//span',
        ).text

        # current_value
        d['current_value'] = portfolio.find_element(by=By.XPATH, value='.//span[@class="instrumentListItem__priceRow"]//span[@class="instrumentListItem__currentPrice"]').text
        d['current_value'] = re.sub(pattern=r' \u20ac|,', repl=r'', string=d['current_value'], flags=0)
        d['current_value'] = float(d['current_value'])

        data.append(d)

    # Create DataFrame
    assets_df = pd.DataFrame(data=data, index=None, dtype=None).filter(
        items=['asset_name', 'isin_code', 'shares', 'current_value'],
    )

    # Metadata
    assets_df = (
        assets_df.assign(date=pd.Timestamp.now().date())
        .assign(type='Investments')
        .assign(financial_institution='Trade Republic')
        .filter(
            items=[
                'date',
                'type',
                'financial_institution',
                'asset_name',
                'isin_code',
                'shares',
                'current_value',
            ],
        )
        .sort_values(
            by=['date', 'financial_institution', 'isin_code'],
            ignore_index=True,
        )
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
            assets_df.to_excel(
                excel_writer=writer,
                sheet_name='Portfolio',
                na_rep='',
                header=True,
                index=False,
                index_label=None,
                freeze_panes=(1, 0),
            )

    elif file_type == '.csv' and output_path is not None:
        assets_df.to_csv(
            path_or_buf=output_path,
            sep=',',
            na_rep='',
            header=True,
            index=False,
            index_label=None,
            encoding='utf-8',
        )

    else:
        assets_df.to_clipboard(excel=True, sep=None, index=False)

    # Quit WebDriver
    if 'driver' in vars():
        driver.quit()

    # Return objects
    if return_df is True:
        return assets_df
