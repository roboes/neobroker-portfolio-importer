"""About: Web-scraping tool to extract and export current portfolio asset information from Trade Republic using Selenium library in Python."""

# Import packages

import re
import time

import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .selenium_utils import selenium_webdriver


# Functions


def trade_republic_portfolio_import(*, login=None, password=None, file_type='.xlsx', output_path=None, return_df=False):
    # Load Selenium WebDriver
    if 'driver' in vars():
        if driver.service.is_connectable() is True:
            pass

    else:
        driver = selenium_webdriver(web_browser='chrome', javascript_disable=True)

    # Open website
    driver.get(url='https://app.traderepublic.com')

    # Cookies: Accept Selected
    try:
        driver.find_element(by=By.XPATH, value='.//form[@class="consentCard__form"]//span[@class="buttonBase__title"]').click()

    except Exception:
        pass

    # Login
    if login is not None and password is not None:
        # Login
        driver.find_element(by=By.XPATH, value="//input[@name='username']").send_keys(str(login), Keys.ENTER)
        time.sleep(1)

        # Password
        driver.find_element(by=By.XPATH, value='//input[@type="password"]').send_keys(int(password), Keys.ENTER)

    else:
        pass

    while True:
        try:
            driver.find_element(by=By.XPATH, value='.//button[@data-testid="rounded-button"][@aria-label="Wealth"]')
            break

        except NoSuchElementException:
            time.sleep(2)

    # Open broker panel
    driver.find_element(by=By.XPATH, value='.//button[@data-testid="rounded-button"][@aria-label="Wealth"]').click()
    time.sleep(2)

    # Click the Brokerage card to expand the instrument list
    driver.find_element(by=By.XPATH, value='.//div[contains(@class,"widgetContainer") and .//span[text()="Brokerage"]]').click()
    time.sleep(3)

    # Get the total count of portfolio items first
    portfolio_elements = driver.find_elements(by=By.XPATH, value='//div[@role="option" and contains(@data-value,"-brokerage")]')
    total_assets = len(portfolio_elements)

    data = []

    for i in range(total_assets):
        # 1. Re-fetch the elements entirely fresh at the exact start of the loop
        portfolio_list = driver.find_elements(by=By.XPATH, value='//div[@role="option" and contains(@data-value,"-brokerage")]')
        portfolio = portfolio_list[i]

        d = {}

        d['asset_name'] = portfolio.find_element(by=By.XPATH, value='.//span[contains(@class,"list-item__title")]').text
        d['isin_code'] = portfolio.get_attribute('data-value').replace('-brokerage', '')

        raw = portfolio.find_element(by=By.XPATH, value='.//span[contains(@class,"list-item__subtitle")]').text
        raw = re.sub(pattern=r'[^\d.]', repl='', string=raw)
        d['current_value'] = float(raw)

        # Click the freshly resolved item
        portfolio.click()

        try:
            shares_el = WebDriverWait(driver=driver, timeout=5).until(
                method=EC.presence_of_element_located(locator=(By.XPATH, '//div[@data-testid="list-row" and .//span[text()="Shares"]]//div[@class="list-row__trailing"]//p'))
            )
            d['shares'] = shares_el.text
        except Exception:
            d['shares'] = None

        # Go back
        time.sleep(2)
        back_button = WebDriverWait(driver=driver, timeout=10).until(method=EC.element_to_be_clickable(mark=(By.XPATH, "//button[@data-testid='panel-back-button']")))
        back_button.click()

        # Wait for the DOM to fully stabilize and display the options list again
        WebDriverWait(driver=driver, timeout=10).until(method=EC.staleness_of(portfolio))
        WebDriverWait(driver=driver, timeout=10).until(method=EC.presence_of_element_located(locator=(By.XPATH, '//div[@role="option" and contains(@data-value,"-brokerage")]')))
        time.sleep(1)

        data.append(d)

    # Create DataFrame
    assets_df = pd.DataFrame(data=data, index=None, dtype=None).filter(items=['asset_name', 'isin_code', 'shares', 'current_value'])

    # Metadata
    assets_df = (
        assets_df.assign(date=pd.Timestamp.now().date())
        .assign(type='Investments')
        .assign(financial_institution='Trade Republic')
        .filter(items=['date', 'type', 'financial_institution', 'asset_name', 'isin_code', 'shares', 'current_value'])
        .sort_values(by=['date', 'financial_institution', 'isin_code'], ignore_index=True)
    )

    # Save
    if file_type == '.xlsx' and output_path is not None:
        with pd.ExcelWriter(
            path=output_path, date_format='YYYY-MM-DD', datetime_format='YYYY-MM-DD HH:MM:SS', engine='xlsxwriter', engine_kwargs={'options': {'strings_to_formulas': False, 'strings_to_urls': False}}
        ) as writer:
            assets_df.to_excel(excel_writer=writer, sheet_name='Portfolio', na_rep='', header=True, index=False, index_label=None, freeze_panes=(1, 0))

    elif file_type == '.csv' and output_path is not None:
        assets_df.to_csv(path_or_buf=output_path, sep=',', na_rep='', header=True, index=False, index_label=None, encoding='utf-8')

    else:
        assets_df.to_clipboard(excel=True, sep=None, index=False)

    # Quit WebDriver
    if 'driver' in vars():
        driver.quit()

    # Return objects
    if return_df is True:
        return assets_df
