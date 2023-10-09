import asyncio
import copy
from urllib import parse

import aiohttp
import nest_asyncio
from tenacity import *

from .async_card import async_card_query
from .async_dataset import async_dataset
from .sync_card import parse_card_question
from .sync_dataset import parse_dataset_question

nest_asyncio.apply()  # To avoid asyncio error


async def export_question_bulk_filter_values(url: str, session: str, bulk_filter_slug: str, bulk_values_list: list, chunk_size=2000, retry_attempts=10, verbose=True, timeout=1800):
    '''
    This function will split bulk_values_list into multiple small values lists, and then send multiple requests to get data, limiting 5 connectors per host.

    To call this function, you need to import asyncio, and then call it by syntax: asyncio.run(export_question_bulk_filter_values()).

    :param url: https://your-domain.com/question/123456-example?your_param_slug=SomeThing or https://your-domain.com/question#eW91cl9xdWVyeQ==
    :param session: Metabase Session
    :param bulk_filter_slug: If URL is a saved question, then get it in URL elif input the Field Name as field_name
    :param bulk_values_list: A list of values that you want to add to the filter
    :param chunk_size: Maximum is 2000
    :param retry_attempts: Number of retry attempts if an error occurs due to server slowdown
    :param verbose: Print the progress
    :param timeout: Timeout for each request
    :return: JSON data
    '''

    if chunk_size > 2000 or chunk_size < 1:
        raise ValueError('chunk_size must be positive and not greater than 2000')

    # Define API endpoint, It would be dataset or card
    parsed_url = parse.urlparse(url=url)
    if 'question' not in parsed_url.path:
        raise ValueError('Please input a question URL')
    api_endpoint = 'dataset' if parsed_url.path == '/question' and parsed_url.fragment else 'card'

    # Split bulk values list to chunks
    bulk_values_lists = [bulk_values_list[i:i + chunk_size] for i in range(0, len(bulk_values_list), chunk_size)]

    # Client session for requesting
    client_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))

    # Parse question to get necessary variables and payload
    if api_endpoint == 'card':
        card_data = parse_card_question(url=url, session=session, bulk_filter_slug=bulk_filter_slug, verbose=verbose)
        domain_url = card_data['domain_url']
        question_id = card_data['question_id']
        parameters = card_data['parameters']
        column_sort_order = card_data['column_sort_order']

        # Create a list of modified parameters
        modified_parameters_list = []
        for bulk_values in bulk_values_lists:
            modified_parameters = []
            for param in parameters:
                if param['target'][-1][-1] == bulk_filter_slug:
                    modified_parameters.append({
                        'type': param['type'],
                        'value': bulk_values,
                        'target': param['target']
                    })
                else:
                    modified_parameters.append(param.copy())
            modified_parameters_list.append(modified_parameters)

    elif api_endpoint == 'dataset':
        table_data = parse_dataset_question(url=url, session=session, bulk_filter_slug=bulk_filter_slug, verbose=verbose)
        domain_url = table_data['domain_url']
        dataset_query = table_data['dataset_query']
        column_sort_order = table_data['column_sort_order']
        bulk_filter_setting = table_data['bulk_filter_setting']

        # Create a list of modified_dataset_query
        modified_dataset_query_list = []
        for bulk_values in bulk_values_lists:
            new_dataset_query = copy.deepcopy(dataset_query)
            new_dataset_query['query']['filter'] += [bulk_filter_setting + bulk_values]
            modified_dataset_query_list.append(new_dataset_query)

    # Handle Retry due to Connection, Timeout, Metabase server slowdown
    async def query_quest(payload, print_suffix=None, verbose=True):
        @retry(stop=stop_after_attempt(retry_attempts), wait=wait_fixed(5), reraise=True)
        async def get_query_data():
            if api_endpoint == 'card':
                return await async_card_query(client_session=client_session,
                                              domain_url=domain_url,
                                              question_id=question_id,
                                              session=session,
                                              parameters=payload,
                                              print_suffix=print_suffix,
                                              verbose=verbose,
                                              timeout=timeout)
            elif api_endpoint == 'dataset':
                return await async_dataset(client_session=client_session,
                                           domain_url=domain_url,
                                           dataset_query=payload,
                                           session=session,
                                           print_suffix=print_suffix,
                                           verbose=verbose,
                                           timeout=timeout)

        # Get data
        query_records = await get_query_data()

        # Raise error by user
        if 'error' in query_records:
            raise Exception(query_records['error'])

        # Sort columns
        if column_sort_order:
            query_records = [{col: item[col] for col in column_sort_order if col in item} for item in query_records]

        if verbose:
            print('Received data', print_suffix)

        return query_records

    # Create multiple async tasks
    tasks = []

    if api_endpoint == 'card':
        total = len(modified_parameters_list)
        counter = 0
        for modified_parameters in modified_parameters_list:
            counter += 1
            tasks.append(asyncio.create_task(query_quest(payload=modified_parameters, print_suffix=f'({counter}/{total})', verbose=verbose)))
            await asyncio.sleep(1)
    elif api_endpoint == 'dataset':
        total = len(modified_dataset_query_list)
        counter = 0
        for modified_dataset_query in modified_dataset_query_list:
            counter += 1
            tasks.append(asyncio.create_task(query_quest(payload=modified_dataset_query, print_suffix=f'({counter}/{total})', verbose=verbose)))
            await asyncio.sleep(1)

    # Combine tasks results
    res = await asyncio.gather(*tasks)
    await client_session.close()

    return sum(res, [])
