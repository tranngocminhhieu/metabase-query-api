# Metabase Query API
Metabase Query API with Retry and Bulk Filter Values.

## Features (pros)
1. Get question data in any data format provided by Metabase (JSON, CSV, XLSX).
2. Input question URL and Metabase Session, no need to provide parameters payload.
3. JSON results have the same column sort order as the browser.
4. Automatically check if Metabase session is available.
5. Allow retry if an error occurs due to server slowdown.
6. Allows entering multiple filter values in bulk, suitable for retrieving data for large number of ids, using asyncio technique.

## Cons
1. Unsaved question URLs are not supported yet.

## Installation


## Instruction
### Import package
```python
from metabase_query_api.sync_query import export_question
from metabase_query_api.async_query import export_question_bulk_filter_values
import asyncio
```

### Get question data
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

```python
bulk_param_slug = 'order_id'
bulk_values_list = ['12345', '67890', '...', '98765']

question_json_data = asyncio.run(export_question_bulk_filter_values(url=url, session=session, bulk_param_slug=bulk_param_slug, bulk_values_list=bulk_values_list))
```