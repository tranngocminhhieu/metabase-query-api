import json
from urllib import parse

import requests
from tenacity import *


def export_query(domain_url: str, question_id, session: str, params: dict, data_format='json', timeout=1800):
    '''

    :param domain_url: https://your-domain.com
    :param question_id: 123456
    :param session: Metabase Session
    :param params: {'parameters': json.dumps(params)}
    :return: JSON data
    '''
    print('Sending request')

    content_type_values = {
        'json': 'application/json',
        'csv': 'text/csv',
        'xlsx': 'application/x-www-form-urlencoded;charset=UTF-8'
    }

    headers = {'Content-Type': content_type_values[data_format], 'X-Metabase-Session': session}

    query_res = requests.post(url=f'{domain_url}/api/card/{question_id}/query/{data_format}', headers=headers, params=params, timeout=timeout)

    if not query_res.ok:
        query_res.raise_for_status()

    retry_error = ['Too many queued queries for "admin"', 'Query exceeded the maximum execution time limit of 5.00m']

    if data_format == 'json':
        query_data = query_res.json()
        if 'error' in query_data:
            if query_data['error'] in retry_error:
                raise Exception(query_data['error'])
            else:
                return {'error': query_data['error']}
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
def parse_question(url: str, session: str, bulk_field_slug: str = None):
    '''
    This function support for export_question and metabase_bulk_request

    :param url: https://your-domain.com/question/123456-example?your_param_slug=SomeThing
    :param session: Metabase Session
    :param bulk_field_slug: The query name in URL that you want to add and filter values run in bulk
    :return: A JSON data of headers, question_id, params, domain_url
    '''
    print('Parsing URL and verifying Metabase Session')

    headers = {'Content-Type': 'application/json', 'X-Metabase-Session': session}

    # Parse URL to get available params, domain, quesion. Also check if session is available.
    parsed_url = parse.urlparse(url=url)
    domain_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    question_id = parsed_url.path.split('/')[-1].split('-')[0]
    query_dict = parse.parse_qs(parsed_url.query)

    card_res = requests.get(url=f'{domain_url}/api/card/{question_id}', headers=headers)

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

    # Build params
    available_params = card_data['parameters']

    ## Add bulk_field_slug
    if bulk_field_slug:
        if bulk_field_slug not in [p['slug'] for p in available_params]:
            raise ValueError('bulk_field_slug is not exist, check the filter slug in URL on browser')
        if bulk_field_slug not in query_dict:
            query_dict[bulk_field_slug] = []

    ## Create params added by user
    params = []
    for k in query_dict:
        for p in available_params:
            if p['slug'] == k:
                param_type = p['type']
                param_target = p['target']
                param_value = query_dict[k]
                if 'number' in param_type:
                    param_value = [float(i) for i in param_value]
                if len(param_value) == 1:
                    param_value = param_value[0]
                param = {'type': param_type, 'value': param_value, 'target': param_target}
                params.append(param)
                break

    ## Get column sort order
    result_metadata = card_data['result_metadata']
    column_sort_order = [col['display_name'] for col in result_metadata]

    card_data = {'headers': headers, 'params': params, 'domain_url': domain_url, 'question_id': question_id, 'column_sort_order': column_sort_order}

    return card_data


def export_question(url: str, session: str, data_format='json', retry_attempts=0):
    '''

    :param url: https://your-domain.com/question/123456-example?your_param_slug=SomeThing
    :param session: Metabase Session
    :param retry_attempts: Number of retry attempts if an error occurs due to server slowdown
    :param data_format: json, csv, xlsx
    :return: JSON data or Bytes data
    '''

    if data_format not in ['json', 'xlsx', 'csv']:
        raise ValueError('Accepted values for data_format are json, xlsx, csv')

    # Parse question
    card_data = parse_question(url=url, session=session)

    domain_url = card_data['domain_url']
    question_id = card_data['question_id']
    params = card_data['params']
    column_sort_order = card_data['column_sort_order']

    # Handle retry due to server slowdown
    @retry(stop=stop_after_attempt(retry_attempts), wait=wait_fixed(5), reraise=True)
    def get_query_data():
        return export_query(domain_url=domain_url, question_id=question_id, session=session, params={'parameters': json.dumps(params)}, data_format=data_format)

    # Get data
    query_data = get_query_data()

    # Check error by user
    if type(query_data) == dict and 'error' in query_data:
        raise Exception(query_data['error'])

    # Order columns for JSON data
    if data_format == 'json':
        query_data = [{col: item[col] for col in column_sort_order} for item in query_data]

    print('Received data')

    return query_data


if __name__ == '__main__':
    session = 'c65f769b-eb4a-4a12-b0be-9596294919fa'
    url = 'https://your-domain.com/question/123456-example?your_param_slug=SomeThing'
    query_data = export_question(url=url, session=session, retry_attempts=5)
    print(query_data)
