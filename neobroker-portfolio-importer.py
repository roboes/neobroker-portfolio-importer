## Neobroker Portfolio Importer
# Last update: 2025-05-15


"""About: Web-scraping tool to extract and export current portfolio asset information from Scalable Capital and Trade Republic using Selenium library in Python."""


###############
# Initial Setup
###############

# Erase all declared global variables
globals().clear()


# Import packages
import os
import re
import time

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Settings

## Set working directory
# os.chdir(path=os.path.join(os.path.expanduser('~'), 'Downloads'))

## Copy-on-Write (will be enabled by default in version 3.0)
if pd.__version__ >= '1.5.0' and pd.__version__ < '3.0.0':
    pd.options.mode.copy_on_write = True


###########
# Functions
###########


def selenium_webdriver(*, web_browser='chrome', headless=False):
    # WebDriver options
    if web_browser == 'chrome':
        webdriver_options = webdriver.ChromeOptions()
        webdriver_options.page_load_strategy = 'eager'
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')
        webdriver_options.add_argument('--disable-search-engine-choice-screen')
        webdriver_options.add_argument('--log-level=3')
        webdriver_options.add_argument('--disable-javascript')
        # webdriver_options.ignore_local_proxy_environment_variables()
        webdriver_options.add_argument('window-size=1920,1080')
        webdriver_options.add_argument('--start-maximized')
        webdriver_options.add_experimental_option(
            'prefs',
            {
                'intl.accept_languages': 'en_us',
                'enable_do_not_track': True,
                # 'download.default_directory': os.path.join(os.path.expanduser('~'), 'Downloads'),
                'download.prompt_for_download': False,
                'profile.default_content_setting_values.automatic_downloads': True,
            },
        )

        if headless is True:
            webdriver_options.add_argument('--headless=new')
            webdriver_options.add_argument('--disable-dev-shm-usage')
            webdriver_options.add_argument('--no-sandbox')
            webdriver_options.add_argument('--user-agent=Mozilla/5.0')
            webdriver_options.add_argument('window-size=1920,1080')
            webdriver_options.add_argument('--start-maximized')

        driver = webdriver.Chrome(options=webdriver_options)

    if web_browser == 'firefox':
        webdriver_options = webdriver.FirefoxOptions()
        webdriver_options.page_load_strategy = 'eager'
        # webdriver_options.set_preference('javascript.enabled', False)
        webdriver_options.set_preference('intl.accept_languages', 'en_us')
        webdriver_options.set_preference('privacy.donottrackheader.enabled', True)
        webdriver_options.set_preference('browser.download.manager.showWhenStarting', False)
        webdriver_options.set_preference('browser.download.dir', os.path.join(os.path.expanduser('~'), 'Downloads'))
        webdriver_options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
        webdriver_options.set_preference('browser.download.folderList', 2)
        webdriver_options.add_argument('--height=1080')
        webdriver_options.add_argument('--start-maximized')

        if headless is True:
            webdriver_options.add_argument('--headless')
            webdriver_options.add_argument('--disable-dev-shm-usage')
            webdriver_options.add_argument('--no-sandbox')
            webdriver_options.set_preference('general.useragent.override', 'Mozilla/5.0')
            webdriver_options.add_argument('--width=1920')
            webdriver_options.add_argument('--height=1080')
            webdriver_options.add_argument('--start-maximized')

        # Firefox About Profiles - about:profiles
        # webdriver_options.add_argument('-profile')
        # webdriver_options.add_argument(os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles', 'nsp3n4ed.default-release'))

        driver = webdriver.Firefox(options=webdriver_options)

    # Return objects
    return driver


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
        driver = selenium_webdriver(web_browser='chrome')

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

    for broker in driver.find_elements(by=By.XPATH, value="//*[text()='Broker']"):
        broker.click()

        time.sleep(2)

        # Trading venues closed
        try:
            driver.find_element(by=By.XPATH, value='.//button[contains(text(), "Close")]').click()

        except Exception:
            pass

        # Portfolio id
        portfolio_id = re.sub(pattern=r'^.*portfolioId=([^&]+).*$', repl=r'\1', string=driver.current_url, flags=0)

        portfolio_section = driver.find_element(by=By.XPATH, value="//h2[text()='Portfolio']/..")

        if 'Start building your portfolio.' in portfolio_section.text:
            continue

        else:
            # Get only security lists for "Portfolio"
            time.sleep(3)
            parent_section = driver.find_element(
                By.XPATH,
                value='.//section[@aria-label="Security list"]',
            )

            # Get 'asset_names' and 'current_values'
            elements = parent_section.find_elements(
                by=By.XPATH,
                value='.//div[@aria-label="grid"]//div[@role="rowgroup"]//div[contains(@class, "jss141")]',
            )

            # Create empty lists
            asset_names = []
            current_values = []

            for element in elements:
                # Split the text content by newline characters
                element = element.text.split('\n')

                asset_names.append(element[0])
                current_values.append(element[1])

            # Delete objects
            del element, elements

            # Get 'isin_codes'
            elements = parent_section.find_elements(
                by=By.XPATH,
                value='.//div[@aria-label="grid"]//div[@role="rowgroup"]//div[contains(@class, "jss141")]//div//a',
            )

            # Create empty list
            isin_codes = []

            for element in elements:
                isin_codes.append(element.get_attribute(name='href'))

            # Delete objects
            del element, elements, parent_section

            # Clean 'isin_codes'
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
        driver = selenium_webdriver(web_browser='chrome')

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
