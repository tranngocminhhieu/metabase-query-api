import asyncio
import json

import aiohttp
import nest_asyncio
from tenacity import *

if __name__ == '__main__':
    from sync_query import parse_question
else:
    from .sync_query import parse_question

nest_asyncio.apply()  # To avoid asyncio error


async def async_query(client_session: object, domain_url: str, question_id, session: str, request_data, print_suffix=None, verbose=True):
    '''
    This API will return maximum 2000 records, this is what you see when run a question on the browser.
    But this API allow sending parameters in data payload, we can add maximum 2000 values in a parameter.
    It only supports content type (data format) JSON.

    :param client_session: asyncio client session
    :param domain_url: https://your-domain.com
    :param question_id: 123456
    :param session: Metabase session
    :param request_data: json.dumps({'parameters': modified_params})
    :param print_suffix: String
    :param verbose: Print progress or not
    :return: JSON data
    '''

    if verbose:
        print('Sending request', print_suffix)

    # Get data
    headers = {'Content-Type': 'application/json', 'X-Metabase-Session': session}

    query_res = await client_session.post(url=f'{domain_url}/api/card/{question_id}/query', headers=headers, data=request_data, timeout=1800)

    # Only raise error: Connection, Timeout, Metabase server slowdown
    # Error by user will be return as a JSON
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

    columns = [col['name'] for col in query_data['cols']]
    rows = query_data['rows']

    query_records = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]

    return query_records


async def export_question_bulk_param_values(url: str, session: str, bulk_param_slug: str, bulk_values_list: list, chunk_size=2000, retry_attempts=10, verbose=True):
    '''
    This function will split bulk_values_list to multiple small values list, and then send multiple request to get data, limit 5 connector per host.

    To call this function, you need to import asyncio, and then call it by syntax: asyncio.run(export_question_bulk_param_values()).

    :param url: https://your-domain.com/question/123456-example?your_param_slug=SomeThing
    :param session: Metabase Session
    :param bulk_param_slug: The field filter slug, get it in URL on browser
    :param bulk_values_list: A list of values that you want to add to filter
    :param chunk_size: Maximum is 2000
    :param retry_attempts: Number of retry attempts if an error occurs due to server slowdown
    :param verbose: Print progress or not
    :return: JSON data
    '''

    if chunk_size > 2000 or chunk_size < 1:
        raise ValueError('chunk_size must be positive and not greater than 2000')

    # Parse question
    card_data = parse_question(url=url, session=session, bulk_param_slug=bulk_param_slug, verbose=verbose)

    domain_url = card_data['domain_url']
    question_id = card_data['question_id']
    params = card_data['params']
    column_sort_order = card_data['column_sort_order']

    # Create a list of modified params
    bulk_values_lists = [bulk_values_list[i:i + chunk_size] for i in range(0, len(bulk_values_list), chunk_size)]

    modified_params_list = []
    for bulk_values in bulk_values_lists:
        modified_params = []
        for param in params:
            if param['target'][-1][-1] == bulk_param_slug:
                modified_params.append({
                    'type': param['type'],
                    'value': bulk_values,
                    'target': param['target']
                })
            else:
                modified_params.append(param.copy())
        modified_params_list.append(modified_params)

    # Client session for requesting
    client_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))

    # Handle retry due to Connection, Timeout, Metabase server slowdown
    async def query_quest(print_suffix=None, verbose=True):
        @retry(stop=stop_after_attempt(retry_attempts), wait=wait_fixed(5), reraise=True)
        async def get_query_data():
            return await async_query(client_session=client_session,
                                     domain_url=domain_url,
                                     question_id=question_id,
                                     session=session,
                                     request_data=json.dumps({'parameters': modified_params}),
                                     print_suffix=print_suffix,
                                     verbose=verbose)

        query_records = await get_query_data()

        if 'error' in query_records:
            raise Exception(query_records['error'])

        query_records = [{col: item[col] for col in column_sort_order} for item in query_records]

        if verbose:
            print('Received data', print_suffix)

        return query_records

    # Create multiple async tasks
    tasks = []
    total = len(modified_params_list)
    counter = 0
    for modified_params in modified_params_list:
        counter += 1
        tasks.append(asyncio.create_task(query_quest(print_suffix=f'({counter}/{total})', verbose=verbose)))
        await asyncio.sleep(1)

    # Combine tasks results
    res = await asyncio.gather(*tasks)
    await client_session.close()

    return sum(res, [])


if __name__ == '__main__':
    session = 'c65f769b-eb4a-4a12-b0be-9596294919fa'
    url = 'https://your-domain.com/question/123456-example?your_param_slug=SomeThing'
    bulk_param_slug = 'id'
    bulk_values_list = []
    result = asyncio.run(export_question_bulk_param_values(url=url, session=session, bulk_param_slug=bulk_param_slug, bulk_values_list=bulk_values_list))
    print(len(result))
