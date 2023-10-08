import json
from urllib import parse

import requests
from tenacity import *


def export_card(domain_url: str, question_id, session: str, parameters, data_format='json', timeout=1800, verbose=True):
    '''
    This function helps get data from a saved question
    To support for Retry feature, it will raise for some connection error and server slowdown error.
    Error by user will be return, for example user forget fill in a required parameter.

    :param domain_url: https://your-domain.com
    :param question_id: 123456
    :param session: Metabase Session
    :param parameters: []
    :param verbose: Print the progress
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

    params = {'parameters': json.dumps(parameters)}

    headers = {'Content-Type': content_type_values[data_format], 'X-Metabase-Session': session}

    query_res = requests.post(url=f'{domain_url}/api/card/{question_id}/query/{data_format}', headers=headers, params=params, timeout=timeout)

    # Only raise error: Connection, Timeout, Metabase server slowdown
    # Error by user will be return as a JSON
    if not query_res.ok:
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

    # XLSX, CSV: Sucesss -> content, error -> JSON
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
def parse_card_question(url: str, session: str, bulk_param_slug: str = None, verbose=True):
    '''
    This function parses the URL to necessary information, that will be used to input for export functions.

    :param url: https://your-domain.com/question/123456-example?your_param_slug=SomeThing
    :param session: Metabase Session
    :param bulk_param_slug: For example order_id
    :param verbose: Print the progress
    :return: question information as JSON
    '''

    if verbose:
        print('Parsing URL and verifying Metabase Session')

    # Parse URL to get variables. Also check if session is available.
    headers = {'Content-Type': 'application/json', 'X-Metabase-Session': session}
    parsed_url = parse.urlparse(url=url)
    domain_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    question_id = parsed_url.path.split('/')[-1].split('-')[0]
    query_dict = parse.parse_qs(parsed_url.query)

    card_res = requests.get(url=f'{domain_url}/api/card/{question_id}', headers=headers)

    ## Raise error
    card_error_dict = {
        401: 'Session is not valid',
        404: 'Question is not exist or you dont have permission',
    }

    if not card_res.ok:
        if card_res.status_code in card_error_dict:
            raise ValueError(card_error_dict.get(card_res.status_code))
        else:
            card_res.raise_for_status()

    card_data = card_res.json()

    ## Get column sort order
    result_metadata = card_data['result_metadata']
    column_sort_order = [col['display_name'] for col in result_metadata]

    # Build parameters
    available_parameters = card_data['parameters']

    ## Add bulk_param_slug
    if bulk_param_slug:
        if bulk_param_slug not in [p['slug'] for p in available_parameters]:
            raise ValueError('bulk_param_slug is not exist, check the filter slug in URL on browser')
        if bulk_param_slug not in query_dict:
            query_dict[bulk_param_slug] = []

    ## Create parameters added by user
    parameters = []
    for k in query_dict:
        for p in available_parameters:
            if p['slug'] == k:
                param_type = p['type']
                param_target = p['target']
                param_value = query_dict[k]
                if 'number' in param_type:
                    param_value = [float(i) for i in param_value]
                if len(param_value) == 1:
                    param_value = param_value[0]
                param = {'type': param_type, 'value': param_value, 'target': param_target}
                parameters.append(param)
                break

    card_data = {'domain_url': domain_url,
                 'question_id': question_id,
                 'parameters': parameters,
                 'column_sort_order': column_sort_order}

    return card_data
