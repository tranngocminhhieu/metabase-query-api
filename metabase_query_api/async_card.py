import json

import nest_asyncio

nest_asyncio.apply()  # To avoid asyncio error


async def async_card_query(client_session: object, domain_url: str, question_id, session: str, parameters: list, print_suffix=None, verbose=True, timeout=1800):
    '''
    This API will return a maximum of 2000 records, this is what you see when running a question on the browser.
    But this API allows sending parameters in data payload, we can add a maximum of 2000 values in a parameter.
    It only supports content type (data format) JSON.

    :param client_session: aiohttp client session
    :param domain_url: https://your-domain.com
    :param question_id: 123456
    :param session: Metabase session
    :param parameters: []
    :param print_suffix: String
    :param verbose: Print progress or not
    :param timeout: Timeout for each request
    :return: JSON data
    '''

    if verbose:
        print('Sending request', print_suffix)

    # Get data
    headers = {'Content-Type': 'application/json', 'X-Metabase-Session': session}
    data = json.dumps({'parameters': parameters})
    query_res = await client_session.post(url=f'{domain_url}/api/card/{question_id}/query', headers=headers, data=data, timeout=timeout)

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
