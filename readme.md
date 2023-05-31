# Neobroker Portfolio Importer

## Description

This web-scraping tool aims to extract portfolio asset information (such as stocks, cryptos and ETFs) from Scalable Capital and Trade Republic, given that both neobrokers currently do not feature a portfolio value export. The main features are:
- Import of portfolio asset of both Scalable Capital and Trade Republic, incl. assets name, ISINs and assets current value.
- Semi-automatic login option, where login and password are automatically filled if user adds the parameters `login` and `password`. It waits until 2FA login confirmation.
- Save of the imported assets as an Excel, .csv or a simply copy it as a table to the system clipboard.

## Privacy

The code runs locally in the user's machine and imitates, via Chrome WebDriver and the Selenium library, user's behavior and extracts the assets information from Scalable Capital and Trade Republic. No information is collected and send externally.

For security reason, it is recommended to keep the default parameters `login = None` and `password = None`.


# Usage

## Python dependencies

```.ps1
python -m pip install lxml openpyxl pandas selenium webdriver-manager
```

## Functions

### scalable_capital_portfolio_import
```.py
scalable_capital_portfolio_import(login=None, password=None, transpose=False, file_type='.xlsx', file_name='Assets Scalable Capital.xlsx')
```

<br>

### trade_republic_portfolio_import
```.py
trade_republic_portfolio_import(login=None, password=None, transpose=False, file_type='.xlsx', file_name='Assets Trade Republic.xlsx')
```

#### Description
- Scraps and imports portfolio asset information from Scalable Capital and Trade Republic.

#### Parameters
- `login`: *str*, default: *None*. If defined (e.g. `login = 'email@email.com'`), login information is automatically filled; otherwise, user needs to manually add them once the WebDriver initiates.
- `password`: *str*, default: *None*. If defined (e.g. `password = '12345'`), password information is automatically filled; otherwise, user needs to manually add them once the WebDriver initiates.
- `transpose`: *bool*, default: *False*. If *True*, imported assets dataset is transposed.
- `path`: *path object*, default user's *'Downloads'* folder.
- `file_type`: *str*, options: *'.xlsx'*, *'.csv'* and *None*, default: *'.xlsx'*. If *None*, imported assets dataset is copied to the system clipboard.
- `file_name`: *str*, default: *'Assets Scalable Capital.xlsx'* (for `scalable_capital_portfolio_import`) and *'Assets Trade Republic.xlsx'* (for `trade_republic_portfolio_import`).

<br>

### selenium_webdriver_quit
```.py
selenium_webdriver_quit()
```

#### Description
- Terminates the WebDriver session.

#### Parameters
- None.
