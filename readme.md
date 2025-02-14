# Neobroker Portfolio Importer

## Description

This web-scraping tool aims to extract portfolio asset information (such as stocks, cryptos and ETFs) from Scalable Capital and Trade Republic, given that both neobrokers currently do not feature a portfolio value export. The main features are:

- Import of portfolio asset of both Scalable Capital and Trade Republic, incl. assets name, ISINs and assets current value.
- Semi-automatic login option, where login and password are automatically filled if user adds the parameters `login` and `password`. It waits until 2FA login confirmation.
- Save of the imported assets as an Excel, .csv or a simply copy it as a table to the system clipboard.

## Privacy

The code runs locally in the user's machine and imitates, via Chrome WebDriver and the Selenium library, user's behavior and extracts the assets information from Scalable Capital and Trade Republic. No information is collected and send externally.

For security reason, it is recommended to keep the default parameters `login = None` and `password = None`.

## Usage

### Python dependencies

```.ps1
python -m pip install lxml openpyxl pandas selenium webdriver-manager xlsxwriter
```

### Functions

#### `scalable_capital_portfolio_import`

```.py
scalable_capital_portfolio_import(login=None, password=None, file_type='.xlsx', output_path=os.path.join(os.path.expanduser('~'), 'Downloads', 'Assets Scalable Capital.xlsx'))
```

<br>

#### `trade_republic_portfolio_import`

```.py
trade_republic_portfolio_import(login=None, password=None, file_type='.xlsx', output_path=os.path.join(os.path.expanduser('~'), 'Downloads', 'Assets Trade Republic.xlsx'))
```

##### Description

- Scraps and imports portfolio asset information from Scalable Capital and Trade Republic.

##### Requirements

- The selected language must be set to `English` for both [Scalable Republic](https://scalable.capital/cockpit/account) and [Trade Republic](https://app.traderepublic.com/settings/appsettings).

##### Parameters

- `login`: _str_, default: _None_. If defined (e.g. `login = 'email@email.com'`), login information is automatically filled; otherwise, user needs to manually add them once the WebDriver initiates.
- `password`: _str_, default: _None_. If defined (e.g. `password = '12345'`), password information is automatically filled; otherwise, user needs to manually add them once the WebDriver initiates.
- `file_type`: _str_, options: _'.xlsx'_, _'.csv'_ and _None_, default: _'.xlsx'_. If _None_, imported assets dataset is copied to the system clipboard.
- `output_path`: _path object_, default: _None_. If _None_, imported assets dataset is copied to the system clipboard.
- `return_df`: _bool_, default: _False_. Returns DataFrame from function.

<br>

#### `selenium_webdriver_quit`

```.py
selenium_webdriver_quit()
```

##### Description

- Terminates the WebDriver session.

##### Parameters

- None.

### Code Workflow Example

```.py
# Scrap, import and save as .csv portfolio asset information from Scalable Capital
scalable_capital_portfolio_import(
    login=None,
    password=None,
    file_type='.xlsx',
    output_path=os.path.join(
        os.path.expanduser('~'),
        'Downloads',
        'Assets Scalable Capital.xlsx',
    ),
    return_df=False,
)

# Scrap, import and save as .csv portfolio asset information from Trade Republic
trade_republic_portfolio_import(
    login=None,
    password=None,
    file_type='.xlsx',
    output_path=os.path.join(
        os.path.expanduser('~'),
        'Downloads',
        'Assets Trade Republic.xlsx',
    ),
    return_df=False,
)

# Quit WebDriver
if 'driver' in vars():
    driver.quit()
```

## See also

[pytr](https://github.com/marzzzello/pytr): Use Trade Republic in terminal.
