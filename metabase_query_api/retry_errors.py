static_errors = [
    'Too many queued queries for "admin"',
    'Query exceeded the maximum execution time limit of 5.00m',
    'Query exceeded the maximum execution time limit of 10.00m',
    'Query exceeded the maximum execution time limit of 15.00m',
    'Query exceeded the maximum execution time limit of 20.00m'
]

dynamic_errors = [
    # Query failed (#20231108_160858_31960_7k6qc): Encountered too many errors talking to a worker node. The node may have crashed or be under too much load. This is probably a transient issue, so please retry your query in a few minutes. (http://10.46.42.18:8080/v1/task/20231108 160858 31960 7k6qc.14.13/results/17/0488 failures, failure duration 300.06s, total failed request time 301.82s)
    'Encountered too many errors talking to a worker node',
    'please retry your query'
    'Query exceeded the maximum execution time limit'
]

def check_retry_errors(error):
    if error in static_errors:
        raise Exception(error)

    for e in dynamic_errors:
        if e in error:
            raise Exception(error)

    return {'error': error}