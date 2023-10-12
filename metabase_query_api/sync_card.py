import json
from urllib import parse

import requests
from tenacity import *


def export_card(domain_url: str, question_id, session: str, parameters, data_format='json', timeout=1800, verbose=True):
    '''
    This function helps get data from a saved question
    To support the Retry feature, it will raise some connection errors and server slowdown errors.
    An error by the user will be returned. For example, the user forgets to fill in a required parameter.

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
def parse_card_question(url: str, session: str, bulk_filter_slug: str = None, verbose=True):
    '''
    This function parses the URL to necessary information, that will be used to input for export functions.

    :param url: https://your-domain.com/question/123456-example?your_param_slug=SomeThing
    :param session: Metabase Session
    :param bulk_filter_slug: For example order_id
    :param verbose: Print the progress
    :return: question information as JSON
    '''

    if verbose:
        print('Parsing URL and verifying Metabase Session')

    # Parse URL to get variables. Also, check if the session is valid.
    headers = {'Content-Type': 'application/json', 'X-Metabase-Session': session}
    parsed_url = parse.urlparse(url=url)
    domain_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    question_id = parsed_url.path.split('/')[-1].split('-')[0]
    query_dict = parse.parse_qs(parsed_url.query)

    card_res = requests.get(url=f'{domain_url}/api/card/{question_id}', headers=headers)

    ## Raise error
    card_error_dict = {
        401: 'Session is not valid',
        404: 'Question is not exist, or you do not have permission',
    }

    if not card_res.ok:
        if card_res.status_code in card_error_dict:
            raise ValueError(card_error_dict.get(card_res.status_code))
        else:
            card_res.raise_for_status()

    card_data = card_res.json()

    ## Get column sort order
    result_metadata = card_data.get('result_metadata')
    if result_metadata:
        column_sort_order = [col['display_name'] for col in result_metadata]
    else:
        print('This query cannot reorder columns for JSON data')
        column_sort_order = None

    # For building parameters
    available_parameters = card_data.get('parameters')
    template_tags = card_data.get('dataset_query').get('native').get('template-tags')

    ## Add bulk_filter_slug
    if bulk_filter_slug:
        if bulk_filter_slug not in [p['slug'] for p in available_parameters]:
            raise ValueError('bulk_filter_slug is not exist, check the filter slug in URL on browser')
        if bulk_filter_slug not in query_dict:
            query_dict[bulk_filter_slug] = []

    ## Create parameters added by user
    parameters = []

    if available_parameters:
        for k in query_dict:
            for p in available_parameters:
                if p['slug'] == k:
                    param_type = p['type']
                    param_target = p['target']
                    param_value = query_dict[k]
                    if 'number' in param_type:
                        param_value = [float(i) for i in param_value]
                    if 'date' in param_type:
                        param_value = param_value[0]
                    param = {'type': param_type, 'value': param_value, 'target': param_target}
                    parameters.append(param)
                    break
    elif template_tags:
        non_dimension_tag_type_to_param_type = {
            'date': 'date/single',
            'number': 'number/=',
            'text': 'category'
        }
        for k in query_dict:
            tag = template_tags[k]
            tag_type = tag['type']

            if tag_type == 'dimension':
                param_type = tag['widget-type']
            else:
                param_type = non_dimension_tag_type_to_param_type[tag_type]

            param_target = [tag_type if tag_type == 'dimension' else 'variable', ['template-tag', k]]

            param_value = query_dict[k]
            if 'number' in param_type:
                param_value = [float(i) for i in param_value]
            if 'date' in param_type:
                param_value = param_value[0]
            param = {'type': param_type, 'value': param_value, 'target': param_target}

            parameters.append(param)

    elif not available_parameters and not template_tags and query_dict:
        raise Exception('Can not build parameters payload for this question, please re-save your question and try again.')

    card_data = {'domain_url': domain_url,
                 'question_id': question_id,
                 'parameters': parameters,
                 'column_sort_order': column_sort_order}

    return card_data
