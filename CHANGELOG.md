# 1.0.1
Change function name from `export_question_bulk_filter_values` to `export_question_bulk_param_values`

# 1.0.0
1. Get question data in any data format provided by Metabase (JSON, CSV, XLSX).
2. Input question URL and Metabase Session, no need to provide parameters payload.
3. JSON results have the same column sort order as the browser.
4. Automatically check if Metabase session is available.
5. Allow retry if an error occurs due to server slowdown.
6. Allows entering multiple filter values in bulk, suitable for retrieving data for large number of ids, using `asyncio` technique.