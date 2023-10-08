# 1.0.4
Change function and parameter name, from `...bulk_param...` to `...bulk_filter...` because the package now support unsaved question URL and users know filter more than param.

# 1.0.3
Support both saved questions (card) and unsaved question (dataset).

# 1.0.2
- Add `verbose` parameter to functions to enable/disable print.
- Fix wrong parameter name in `parse_question` function (`bulk_param_slug`).
- Add more comments and function descriptions.

# 1.0.1
Change function name from `export_question_bulk_filter_values` to `export_question_bulk_param_values`

# 1.0.0
1. Get question data in any data format provided by Metabase (JSON, CSV, XLSX).
2. Input question URL and Metabase Session, no need to provide parameters payload.
3. JSON results have the same column sort order as the browser.
4. Automatically check if Metabase session is available.
5. Allow retry if an error occurs due to server slowdown.
6. Allows entering multiple param values in bulk, suitable for retrieving data for large number of ids, using `asyncio` technique.