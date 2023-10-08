# Metabase Query API
[![Downloads](https://img.shields.io/pypi/dm/metabase-query-api)](https://pypi.org/project/metabase-query-api)
[![Pypi](https://img.shields.io/pypi/v/metabase-query-api)](https://pypi.org/project/metabase-query-api)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/tranngocminhhieu/metabase-query-api/issues)
[![MIT](https://img.shields.io/github/license/tranngocminhhieu/metabase-query-api)](https://github.com/tranngocminhhieu/metabase-query-api/blob/main/LICENSE)

This package will help Data workers get data from [Metabase](https://www.metabase.com/) questions more easily and effectively. It only focuses on the [Card Query API](https://www.metabase.com/docs/latest/api/card#post-apicardcard-idqueryexport-format) and does not include other Metabase APIs.

## Features
1. Get question data in any data format provided by Metabase (JSON, CSV, XLSX).
2. Input question URL and Metabase Session, no need to provide parameters payload.
3. JSON results have the same column sort order as the browser.
4. Automatically check if Metabase session is available.
5. Allow retry if an error occurs due to server slowdown.
6. Allows entering multiple param values in bulk, suitable for retrieving data for a large number of ids, using `asyncio` technique.
7. Support both saved questions (card) and unsaved question (dataset).

## Installation
```commandline
pip install metabase-query-api
```


## Instruction
### Import package
```python
from metabase_query_api.sync_query import export_question
from metabase_query_api.async_query import export_question_bulk_param_values
import asyncio
```

### Get question data
- Copy the question URL in the browser, note that you must fill in the necessary params before copying.
- Use a different API to get the [Metabase Session](https://www.metabase.com/docs/latest/api/session#post-apisession). Or you can use this [Chrome extension](https://chrome.google.com/webstore/detail/cookie-tab-viewer/fdlghnedhhdgjjfgdpgpaaiddipafhgk) to get it.

**Special parameters:**
- `retry_attempts` defaults to `0`, use it when your Metabase server is often slow.
- `data_format` defaults to `'json'`, accepted values are `'json'`, `'csv'`, `'xlsx'`.
#### Export question data to a JSON variable

```python
session = 'c65f769b-eb4a-4a12-b0be-9596294919fa'

# Saved question URL
url = 'https://your-domain.com/question/123456-example?your_param_slug=SomeThing'
# Unsaved question URL
url = 'https://your-domain.com/question#eW91cl9xdWVyeQ=='

question_json_data = export_question(url=url, session=session, retry_attempts=5)
```

#### Export question data to an Excel file
```python
question_xlsx_data = export_question(url=url, session=session, data_format='xlsx', retry_attempts=5)
with open('Excel_file.xlsx', 'wb') as file:
    file.write(question_xlsx_data)
```

#### Export question data to a CSV file
```python
question_csv_data = export_question(url=url, session=session, data_format='csv', retry_attempts=5)
with open('CSV_file.csv', 'wb') as file:
    file.write(question_csv_data)
```

### Get question data with bulk param values
This function is suitable for retrieving data with a large number of values that need to be filled in a param, usually an id field.

It will split your list of values into multiple parts, each containing up to 2000 values.

It then sends multiple asynchronous requests to get the data. Once completed, the data pieces will be merged into one.

**⚠️ Note:** Using this function may slow down your Metabase server.

**Special parameters:**
- `bulk_param_slug`: Saved question -> parameter slug in URL, unsaved question -> Field Name as field_name.
- `bulk_values_list` is a list of values.
- `chunk_size` default and the maximum is  `2000`. If your data has duplicates for each filter value, reduce the chunk size. Because each piece of data only contains 2000 lines.
- `retry_attempts` defaults to `10`, use it when your Metabase server is often slow.
```python
session = 'c65f769b-eb4a-4a12-b0be-9596294919fa'

# Saved question URL
url = 'https://your-domain.com/question/123456-example?your_param_slug=SomeThing'
# Unsaved question URL
url = 'https://your-domain.com/question#eW91cl9xdWVyeQ=='

bulk_param_slug = 'order_id'
bulk_values_list = ['12345', '...', '98765']

question_json_data = asyncio.run(export_question_bulk_param_values(url=url, session=session, bulk_param_slug=bulk_param_slug, bulk_values_list=bulk_values_list, chunk_size=2000))

# Save to CSV/Excel file
import pandas as pd

df = pd.DataFrame(question_json_data)

df.to_csv('file.csv', index=False)
df.to_excel('file.xlsx', index=False)
```
