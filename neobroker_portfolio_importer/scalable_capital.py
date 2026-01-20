"""About: Web-scraping tool to extract and export current portfolio asset information from Scalable Capital using Selenium library in Python."""

# Import packages

import re
import time

import pandas as pd
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .selenium_utils import selenium_webdriver


# Settings


## Copy-on-Write (will be enabled by default in version 3.0)
if pd.__version__ >= '1.5.0' and pd.__version__ < '3.0.0':
    pd.options.mode.copy_on_write = True


# Functions


def scalable_capital_portfolio_import(
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
                # "Welcome to the new Scalable" page
                if 'auth/custodian-switch/successful-migration' in driver.current_url:
                    try:
                        driver.find_element(by=By.CSS_SELECTOR, value='[data-testid="custodian_switch_successful_migration_cta"]').click()

                    except NoSuchElementException:
                        pass

                WebDriverWait(driver=driver, timeout=2).until(EC.url_contains('cockpit'))
                break

            except TimeoutException:
                time.sleep(1)

    # Cookies: Only essentials
    time.sleep(3)
    try:
        driver.execute_script(
            script="""return document.querySelector("#usercentrics-root").shadowRoot.querySelector("button[data-testid='uc-deny-all-button']")""",
        ).click()

    except Exception:
        pass

    # Open broker
    driver.get(url='https://de.scalable.capital/broker/')
    time.sleep(5)

    # Trading venues closed
    try:
        driver.find_element(by=By.XPATH, value='.//button[contains(text(), "Close")]').click()

    except Exception:
        pass

    # PRIME+ Broker
    try:
        driver.find_element(by=By.XPATH, value='//button[@data-testid="close-modal-button"]').click()

    except Exception:
        pass

    # Security lists ("Portfolio" and "Watchlist")
    # security_lists = driver.find_elements(by=By.XPATH, value='.//section[@aria-label="Security list"]//header//div//h2')

    # Create empty DataFrame
    assets_df = pd.DataFrame(data=None, index=None, dtype='str')

    # Trading venues closed
    try:
        driver.find_element(by=By.XPATH, value='.//button[contains(text(), "Close")]').click()

    except Exception:
        pass

    # Portfolio id
    portfolio_id = re.sub(pattern=r'^.*portfolioId=([^&]+).*$', repl=r'\1', string=driver.current_url, flags=0)

    portfolio_section = driver.find_element(by=By.XPATH, value="//h2[text()='Portfolio']/..")

    if 'Popular savings plans' in portfolio_section.text:
        pass

    else:
        # Get only security lists for "Portfolio"
        time.sleep(3)

        # Get 'asset_names', 'current_values' and 'isin_codes'
        elements = driver.find_element(by=By.XPATH, value='//div[@aria-label="Portfolio"]//div')
        elements = elements.find_elements(by=By.TAG_NAME, value='li')

        ## Create empty lists
        asset_names = []
        current_values = []
        isin_codes = []

        for element in elements:
            asset_names.append(element.find_element(by=By.CSS_SELECTOR, value='div[data-testid="text"]').text.strip())
            current_values.append(element.find_element(by=By.CSS_SELECTOR, value='div[aria-label="Total value"] span').text.strip())
            isin_codes.append(element.find_element(by=By.CSS_SELECTOR, value='a').get_attribute('href'))

        ## Delete objects
        del element, elements

        ## Clean 'isin_codes'
        isin_codes = [re.sub(pattern=r'https://de.scalable.capital/broker/security\?isin=|&portfolioId=.*', repl=r'', string=isin_code, flags=0) for isin_code in isin_codes]

        # Import portfolio
        assets_import_df = (
            pd.DataFrame(data={'asset_name': asset_names, 'isin_code': isin_codes, 'current_value': current_values}, index=None, dtype=None)
            # current_value
            .assign(current_value=lambda row: row['current_value'].replace(to_replace=r'(^.*\u20ac)([0-9]+,[0-9]+\.[0-9]+|[0-9]+\.[0-9]+)(.*)?', value=r'\2', regex=True))
            .assign(current_value=lambda row: row['current_value'].replace(to_replace=r',', value=r'', regex=False))
            # .astype(dtype={'current_value': 'float'})
            .filter(items=['asset_name', 'isin_code', 'shares', 'current_value'])
        )

        # Delete objects
        del asset_names, current_values

        # shares
        shares = []

        for isin_code in isin_codes:
            driver.get(url=f'https://de.scalable.capital/broker/security?isin={isin_code}&portfolioId={portfolio_id}')

            # Wait until the element with the text "Shares" is found
            WebDriverWait(driver=driver, timeout=10).until(method=EC.presence_of_element_located(locator=(By.XPATH, '//div[contains(text(), "Shares")]//..//span')))

            share_value = driver.find_element(by=By.XPATH, value='//div[contains(text(), "Shares")]//..//span').text
            share_value = re.sub(pattern=r'^\u20ac|,', repl=r'', string=share_value, flags=0)
            share_value = float(share_value)
            shares.append({'isin_code': isin_code, 'shares': share_value})

        # Create DataFrame
        shares_df = pd.DataFrame(data=shares, index=None, dtype=None)

        # Left join 'assets_import_df' with 'shares_df'
        assets_import_df = pd.merge(left=assets_import_df, right=shares_df, how='left', on=['isin_code'], indicator=False).filter(items=['asset_name', 'isin_code', 'shares', 'current_value'])

        # Delete objects
        del isin_codes, shares, shares_df

        # Metadata
        assets_import_df = (
            assets_import_df.assign(date=pd.Timestamp.now().date())
            .assign(type='Investments')
            .assign(financial_institution='Scalable Capital')
            .filter(items=['date', 'type', 'financial_institution', 'asset_name', 'isin_code', 'shares', 'current_value'])
            .sort_values(by=['date', 'financial_institution', 'isin_code'], ignore_index=True)
        )

        # Concatenate DataFrame
        assets_df = pd.concat(objs=[assets_df, assets_import_df], axis=0, ignore_index=False, sort=False)

        # Delete objects
        del assets_import_df

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
