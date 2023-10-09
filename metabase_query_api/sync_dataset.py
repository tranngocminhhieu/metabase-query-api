import base64
import json
from urllib import parse

import requests
from tenacity import *


def export_dataset(domain_url: str, dataset_query: dict, session: str, data_format='json', verbose=True, timeout=1800):
    '''
    This function helps get data from an unsaved question.
    To support the Retry feature, it will raise some connection errors and server slowdown errors.
    An error by the user will be returned. For example, the user forgets to fill in a required parameter.

    :param domain_url: https://your-domain.com
    :param dataset_query: JSON query
    :param session: Metabase session
    :param data_format: Accepted values are json, xlsx, csv
    :param verbose: Print the progress
    :param timeout: Timeout for each request
    :return: JSON or Bytes data
    '''
    if verbose:
        print('Sending request')

    # Get data from Metabase
    content_type_values = {
        'json': 'application/json',
        'csv': 'text/csv',
        'xlsx': 'application/x-www-form-urlencoded;charset=UTF-8'
    }

    headers = {'Content-Type': content_type_values[data_format], 'X-Metabase-Session': session}

    params = {'query': json.dumps(dataset_query)}

    query_res = requests.post(url=f'{domain_url}/api/dataset/{data_format}',
                              headers=headers,
                              params=params,
                              timeout=timeout)

    # Only raise error: Connection, Timeout, Metabase server slowdown
    # Error by the user will be returned as a JSON
    if not query_res.ok:
        if query_res.status_code == 414:
            return {'error': 'URI is too long. Please do not add values to the filter in bulk. If you need such a filter, then use the export_question_bulk_filter_values function.'}
        else:
            query_res.raise_for_status()

    retry_error = ['Too many queued queries for "admin"', 'Query exceeded the maximum execution time limit of 5.00m']

    # JSON
    if data_format == 'json':
        query_data = query_res.json()
        if 'error' in query_data:
            if query_data['error'] in retry_error:
                raise Exception(query_data['error'])
            else:
                return {'error': query_data['error']}

    # XLSX, CSV: Success -> content, error -> JSON
    else:
        query_data = query_res.content
        if b'"error":' in query_data:
            query_data = query_res.json()
            if query_data['error'] in retry_error:
                raise Exception(query_data['error'])
            else:
                return {'error': query_data['error']}

    return query_data


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
def parse_dataset_question(url: str, session: str, bulk_filter_slug: str = None, verbose=True):
    '''
    This function parses the URL to necessary information, that will be used to input for export functions.

    :param url: https://your-domain.com/question#eW91cl9xdWVyeQ==
    :param session: Metabase session
    :param bulk_filter_slug: For example order_id
    :param verbose: Print the progress
    :return: question information as JSON
    '''

    if verbose:
        print('Parsing URL and verifying Metabase Session')

    # Parse URL to get variables. Also, check if the session is available.
    headers = {'Content-Type': 'application/json', 'X-Metabase-Session': session}
    parsed_url = parse.urlparse(url=url)
    domain_url = f'{parsed_url.scheme}://{parsed_url.netloc}'  # > export functions
    query = json.loads(base64.b64decode(parsed_url.fragment))
    dataset_query = query['dataset_query']  # > export functions
    source_table = dataset_query['query']['source-table']

    table_res = requests.get(url=f'{domain_url}/api/table/{source_table}/query_metadata', headers=headers)

    ## Raise error
    card_error_dict = {
        401: 'Session is not valid',
        404: 'Table does not exist or you do not have permission',
    }

    if not table_res.ok:
        if table_res.status_code in card_error_dict:
            raise ValueError(card_error_dict.get(table_res.status_code))
        else:
            table_res.raise_for_status()

    query_metadata = table_res.json()

    ## Get column sort order
    fields = query_metadata['fields']
    column_sort_order = [col['display_name'] for col in fields]

    # Rebuild dataset_query if bulk_filter_slug
    if bulk_filter_slug:
        ## Find the bulk_filter_id and create bulk_filter_setting
        bulk_filter_id = [f['id'] for f in fields if f['name'] == bulk_filter_slug]
        if not bulk_filter_id:
            raise ValueError('bulk_filter_slug is not exist in fields')
        else:
            bulk_filter_id = bulk_filter_id[0]
        bulk_filter_setting = ['=', ['field', bulk_filter_id, None]]

        ## Make sure the query has a filter and does not include the filter of bulk_filter_id
        ## We will add bulk_filter_setting with values in an async export function
        if 'filter' not in dataset_query['query']:
            dataset_query['query']['filter'] = ['and']
        else:
            dataset_query['query']['filter'] = ['and'] + [f for f in dataset_query['query']['filter'][1:] if f[1][1] != bulk_filter_id]
    else:
        bulk_filter_id = None
        bulk_filter_setting = None

    table_data = {'domain_url': domain_url,
                  'dataset_query': dataset_query,
                  'source_table': source_table,
                  'column_sort_order': column_sort_order,
                  'bulk_filter_id': bulk_filter_id,
                  'bulk_filter_setting': bulk_filter_setting}

    return table_data
