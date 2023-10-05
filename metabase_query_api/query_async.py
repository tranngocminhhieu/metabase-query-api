import asyncio
import json

import aiohttp
import nest_asyncio
from tenacity import *

if __name__ == '__main__':
    from query_sync import metabase_card_info
else:
    from .query_sync import metabase_card_info

nest_asyncio.apply()  # To avoid asyncio error


async def metabase_query_async(client_session: object, domain_url: str, question_id, headers: dict, request_data, print_suffix=None):
    print('Sending request', print_suffix)

    query_res = await client_session.post(url=f'{domain_url}/api/card/{question_id}/query', headers=headers, data=request_data, timeout=1800)

    if not query_res.ok:
        query_res.raise_for_status()

    query_data = await query_res.json()

    retry_error = ['Too many queued queries for "admin"', 'Query exceeded the maximum execution time limit of 5.00m']

    if 'error' in query_data:
        if query_data['error'] in retry_error:
            raise Exception(query_data['error'])
        else:
            return {'error': query_data['error']}

    query_data = query_data['data']

    columns = [col['name'] for col in query_data['cols']]
    rows = query_data['rows']

    query_records = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]

    return query_records


async def metabase_bulk_request(url: str, session: str, bulk_field_slug: str, bulk_values_list: list, chunk_size=2000, retry_attempts=10):
    '''

    :param url: https://your-domain.com/question/123456-example?your_filter=SomeThing
    :param session: Metabase Session
    :param bulk_field_slug:
    :param bulk_values_list:
    :param chunk_size: Maximum is 2000
    :param retry_attempts: Number of retry attempts when error by server slowing
    :return:
    '''
    client_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))

    card_data = metabase_card_info(url=url, session=session, bulk_field_slug=bulk_field_slug)

    domain_url = card_data['domain_url']
    question_id = card_data['question_id']
    headers = card_data['headers']
    params = card_data['params']

    # Create a list of modified params
    bulk_values_lists = [bulk_values_list[i:i + chunk_size] for i in range(0, len(bulk_values_list), chunk_size)]

    modified_params_list = []
    for bulk_values in bulk_values_lists:
        modified_params = []
        for param in params:
            if param['target'][-1][-1] == bulk_field_slug:
                modified_params.append({
                    'type': param['type'],
                    'value': bulk_values,
                    'target': param['target']
                })
            else:
                modified_params.append(param.copy())
        modified_params_list.append(modified_params)

    async def query_quest(print_suffix=None):
        @retry(stop=stop_after_attempt(retry_attempts), wait=wait_fixed(5), reraise=True)
        async def get_query_data():
            return await metabase_query_async(client_session=client_session,
                                              domain_url=domain_url,
                                              question_id=question_id,
                                              headers=headers,
                                              request_data=json.dumps({'parameters': modified_params}),
                                              print_suffix=print_suffix)

        query_records = await get_query_data()

        if 'error' in query_records:
            raise Exception(query_records['error'])

        print('Received data', print_suffix)

        return query_records

    tasks = []
    total = len(modified_params_list)
    counter = 0
    for modified_params in modified_params_list:
        counter += 1
        tasks.append(asyncio.create_task(query_quest(print_suffix=f'({counter}/{total})')))
        await asyncio.sleep(1)

    res = await asyncio.gather(*tasks)
    await client_session.close()

    return sum(res, [])

if __name__ == '__main__':
    session = 'c65f769b-eb4a-4a12-b0be-9596294919fa'
    url = 'https://your-domain/question/83789-test-api?run=1'
    bulk_field_slug = 'tracking_id'
    bulk_values_list = []
    result = asyncio.run(metabase_bulk_request(url=url, session=session, bulk_field_slug=bulk_field_slug, bulk_values_list=bulk_values_list))
    print(len(result))