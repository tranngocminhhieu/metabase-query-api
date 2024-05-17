# 1.1.1
- `export_question_bulk_filter_values` will return successful paths if there were error paths.
- Add `export_question_bulk_filter_values` and `export_question` to the `__init__.py` so you can import shorter.

# 1.1.0
Fix custom_retry_errors is not used in async_query.

# 1.0.9
Add check_retry_errors function for checking static errors and dynamic errors.

# 1.0.8
Can not build parameters payload for old queries due to Card API don't give parameters values. Use template-tags as an alternative method to build parameters payload, also raise an error if both parameters and template-tags is None in Card API data, It is simply fix by re-save the question. ([Issue #5](https://github.com/tranngocminhhieu/metabase-query-api/issues/5)) 

# 1.0.7
Fix error: `Invalid values provided for operator: :string/=` when input only 1 value in param.

# 1.0.6
- Avoid error for some queries that do not have `column_sort_order` ([Issue #3](https://github.com/tranngocminhhieu/metabase-query-api/issues/3)).
- 414 error should be returned instead of retry ([Issue #1](https://github.com/tranngocminhhieu/metabase-query-api/issues/1)).

# 1.0.5
Clean code

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