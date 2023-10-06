# Metabase Query API
This package will help Data workers get data from [Metabase](https://www.metabase.com/) questions more easily and effectively. It only focuses on the [Card Query API](https://www.metabase.com/docs/latest/api/card#post-apicardcard-idqueryexport-format) and does not include other Metabase APIs.

## Features (pros)
1. Get question data in any data format provided by Metabase (JSON, CSV, XLSX).
2. Input question URL and Metabase Session, no need to provide parameters payload.
3. JSON results have the same column sort order as the browser.
4. Automatically check if Metabase session is available.
5. Allow retry if an error occurs due to server slowdown.
6. Allows entering multiple filter values in bulk, suitable for retrieving data for large number of ids, using `asyncio` technique.

## Cons
1. Unsaved question URLs are not supported yet.
2. Bulk filter values with `asyncio` only supports SQL query questions.

## Installation
```commandline
pip install metabase-query-api
```


## Instruction
### Import package
```python
from metabase_query_api.sync_query import export_question
from metabase_query_api.async_query import export_question_bulk_filter_values
import asyncio
```

### Get question data
- Copy the question URL in the browser, note that you must fill in the necessary filters before copying.
- Use a different API to get the [Metabase Session](https://www.metabase.com/docs/latest/api/session#post-apisession). Or you can use this [Chrome extension](https://chrome.google.com/webstore/detail/cookie-tab-viewer/fdlghnedhhdgjjfgdpgpaaiddipafhgk) to get it.

**Special parameters:**
- `retry_attempts` defaults to `0`, use it when your Metabase server is often slow.
- `data_format` defaults to `'json'`, accepted values are `'json'`, `'csv'`, `'xlsx'`.
#### Export question data to a JSON variable

```python
session = 'c65f769b-eb4a-4a12-b0be-9596294919fa'
url = 'https://your-domain.com/question/123456-example?your_param_slug=SomeThing'

question_json_data = export_question(url=url, session=session, retry_attempts=5)
```

#### Export question data to a Excel file
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

### Get question data with multiple filter values in bulk
This function is suitable for retrieving data with a large number of values that need to be filled in a param, usually an id field.

It will split your list of values into multiple parts, each containing up to 2000 values.

It then sends multiple asynchronous requests to get the data. Once completed, the data pieces will be merged into one.

**Note:** Using this function may slow down your Metabase server.

**Special parameters:**
- `bulk_param_slug` is the parameters slug in URL.
- `bulk_values_list` is a list of values.
- `chunk_size` default and maximum is  `2000`. If your data has duplicates for each filter value, reduce the chunk size. Because each piece of data only contains 2000 lines.
- `retry_attempts` defaults to `10`, use it when your Metabase server is often slow.
```python
session = 'c65f769b-eb4a-4a12-b0be-9596294919fa'
url = 'https://your-domain.com/question/123456-example?your_param_slug=SomeThing'
bulk_param_slug = 'order_id'
bulk_values_list = ['12345', '...', '98765']

question_json_data = asyncio.run(export_question_bulk_filter_values(url=url, session=session, bulk_param_slug=bulk_param_slug, bulk_values_list=bulk_values_list, chunk_size=2000))
```