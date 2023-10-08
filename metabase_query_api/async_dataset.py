import json


async def async_dataset(client_session: object, domain_url: str, dataset_query: dict, session: str, print_suffix=None, verbose=True, timeout=1800):
    '''
    This API will return a maximum of 2000 records, and this is what you see when you run a question on the browser.
    But this API allows sending parameters in data payload, and we can add a maximum of 2000 values in a parameter.
    It only supports content type (data format) JSON.

    :param client_session: aiohttp.ClientSession
    :param domain_url: https://your-domain.com
    :param dataset_query: JSON payload
    :param session: Metabase session
    :param print_suffix: String
    :param verbose: Print the progress
    :param timeout: Timeout for each request
    :return: JSON data
    '''

    if verbose:
        print('Sending request', print_suffix)

    # Get data
    headers = {'Content-Type': 'application/json', 'X-Metabase-Session': session}
    data = json.dumps(dataset_query)
    query_res = await client_session.post(url=f'{domain_url}/api/dataset', headers=headers, data=data, timeout=timeout)

    # Only raise error: Connection, Timeout, Metabase server slowdown
    # Error by the user will be returned as a JSON
    if not query_res.ok:
        query_res.raise_for_status()

    query_data = await query_res.json()

    retry_error = ['Too many queued queries for "admin"', 'Query exceeded the maximum execution time limit of 5.00m']

    if 'error' in query_data:
        if query_data['error'] in retry_error:
            raise Exception(query_data['error'])
        else:
            return {'error': query_data['error']}

    # Convert data to records (JSON)
    query_data = query_data['data']

    columns = [col['display_name'] for col in query_data['cols']]
    rows = query_data['rows']

    query_records = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]

    return query_records
