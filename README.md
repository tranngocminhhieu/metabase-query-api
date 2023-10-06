# metabase_query_api
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