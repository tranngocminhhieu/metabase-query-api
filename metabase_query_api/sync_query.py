from urllib import parse

from tenacity import *

from .sync_card import export_card, parse_card_question
from .sync_dataset import export_dataset, parse_dataset_question


def export_question(url: str, session: str, data_format='json', retry_attempts=0, verbose=True, timeout=1800):
    '''
    This function helps users get data from a question URL and a Metabase cookie.
    It supports Retry to help the user retry when a connection error or Metabase sever slowdown occurs.

    :param url: https://your-domain.com/question/123456-example?your_param_slug=SomeThing or https://your-domain.com/question#eW91cl9xdWVyeQ==
    :param session: Metabase Session
    :param retry_attempts: Number of retry attempts if an error occurs due to server slowdown
    :param data_format: json, csv, xlsx
    :param verbose: Print the progress
    :param timeout: Timeout for each request
    :return: JSON data or Bytes data
    '''

    # Check if the data format is right
    if data_format not in ['json', 'xlsx', 'csv']:
        raise ValueError('Accepted values for data_format are json, xlsx, csv')

    # Define API endpoint
    parsed_url = parse.urlparse(url=url)
    if 'question' not in parsed_url.path:
        raise ValueError('Please input a question URL')
    api_endpoint = 'dataset' if parsed_url.path == '/question' and parsed_url.fragment else 'card'

    # Get variables
    if api_endpoint == 'dataset':
        table_data = parse_dataset_question(url=url, session=session, verbose=verbose)
        domain_url = table_data['domain_url']
        dataset_query = table_data['dataset_query']
        column_sort_order = table_data['column_sort_order']
    elif api_endpoint == 'card':
        card_data = parse_card_question(url=url, session=session, verbose=verbose)
        domain_url = card_data['domain_url']
        question_id = card_data['question_id']
        parameters = card_data['parameters']
        column_sort_order = card_data['column_sort_order']

    # Handle retry due to Connection, Timeout, Metabase server slowdown
    @retry(stop=stop_after_attempt(retry_attempts), wait=wait_fixed(5), reraise=True)
    def get_query_data():
        if api_endpoint == 'dataset':
            return export_dataset(domain_url=domain_url, dataset_query=dataset_query, session=session, data_format=data_format, verbose=verbose, timeout=timeout)
        elif api_endpoint == 'card':
            return export_card(domain_url=domain_url, question_id=question_id, parameters=parameters, session=session, data_format=data_format, verbose=verbose, timeout=timeout)

    # Get data
    query_data = get_query_data()

    # Check error by the user
    if type(query_data) == dict and 'error' in query_data:
        raise Exception(query_data['error'])

    # Order columns for JSON data
    if data_format == 'json' and column_sort_order:
        query_data = [{col: item[col] for col in column_sort_order if col in item} for item in query_data]

    if verbose:
        print('Received data')

    return query_data
