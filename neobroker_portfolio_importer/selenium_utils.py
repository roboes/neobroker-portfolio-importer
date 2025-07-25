"""About: Selenium configuration and helper function for web scraping."""

# Import packages

import os
from typing import Literal

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.proxy import Proxy, ProxyType


# Functions


def selenium_webdriver(*, web_browser: Literal['chrome', 'firefox'] = 'chrome', user_agent: str = 'Mozilla/5.0', headless: bool = False, javascript_disable: bool = False, proxy_disable: bool = False) -> WebDriver:
    # WebDriver options
    if web_browser == 'chrome':
        webdriver_options = webdriver.ChromeOptions()
        webdriver_options.page_load_strategy = 'eager'
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')
        webdriver_options.add_argument('--disable-search-engine-choice-screen')
        webdriver_options.add_argument('--log-level=3')
        webdriver_options.add_experimental_option(
            'prefs',
            {
                'intl.accept_languages': 'en_us',
                'enable_do_not_track': True,
                'download.default_directory': os.path.join(os.path.expanduser('~'), 'Downloads'),
                'download.prompt_for_download': False,
                'profile.default_content_setting_values.automatic_downloads': True,
            },
        )

        if headless is True:
            webdriver_options.add_argument('--headless=new')
            webdriver_options.add_argument('--disable-dev-shm-usage')
            webdriver_options.add_argument('--no-sandbox')
            webdriver_options.add_argument(f'--user-agent={user_agent}')
            webdriver_options.add_argument('window-size=1920,1080')

        else:
            webdriver_options.add_argument('--start-maximized')

        if javascript_disable:
            webdriver_options.add_argument('--disable-javascript')

        if proxy_disable:
            proxy = Proxy()
            proxy.proxy_type = ProxyType.DIRECT
            webdriver_options.proxy = proxy

        driver = webdriver.Chrome(options=webdriver_options)

    if web_browser == 'firefox':
        webdriver_options = webdriver.FirefoxOptions()
        webdriver_options.page_load_strategy = 'eager'
        webdriver_options.set_preference('intl.accept_languages', 'en-US')
        webdriver_options.set_preference('privacy.donottrackheader.enabled', True)
        webdriver_options.set_preference('browser.download.manager.showWhenStarting', False)
        webdriver_options.set_preference('browser.download.dir', os.path.join(os.path.expanduser('~'), 'Downloads'))
        webdriver_options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
        webdriver_options.set_preference('browser.download.folderList', 2)

        if headless is True:
            webdriver_options.add_argument('--headless')
            webdriver_options.add_argument('--disable-dev-shm-usage')
            webdriver_options.add_argument('--no-sandbox')
            webdriver_options.set_preference('general.useragent.override', f'{user_agent}')
            webdriver_options.add_argument('--width=1920')
            webdriver_options.add_argument('--height=1080')

        else:
            webdriver_options.add_argument('--start-maximized')

        if javascript_disable:
            webdriver_options.set_preference('javascript.enabled', False)

        if proxy_disable:
            webdriver_options.set_preference('network.proxy.type', ProxyType.DIRECT.value)

        # Firefox About Profiles - about:profiles
        # webdriver_options.add_argument('-profile')
        # webdriver_options.add_argument(os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles', 'nsp3n4ed.default-release'))

        driver = webdriver.Firefox(options=webdriver_options)

    # Return objects
    return driver
