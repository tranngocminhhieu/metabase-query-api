presto_errors = [
    # Static errors:
    'Too many queued queries for "admin"',
    'Error executing query',

    # Dynamic errors:
    'Query exceeded the maximum execution time limit', # Query exceeded the maximum execution time limit of 5.00m
    'Max requests queued per destination', # Max requests queued per destination 1024 exceeded for HttpDestination[http://10.46.23.9:8080]@56f7d1bb,queue=1024,pool=DuplexConnectionPool@15a86dc3[c=1/250/250,a=249,i=0]
    'Encountered too many errors talking to a worker node' # Query failed (#20231108_160858_31960_7k6qc): Encountered too many errors talking to a worker node. The node may have crashed or be under too much load. This is probably a transient issue, so please retry your query in a few minutes. (http://10.46.42.18:8080/v1/task/20231108 160858 31960 7k6qc.14.13/results/17/0488 failures, failure duration 300.06s, total failed request time 301.82s)
]

def check_retry_errors(error, custom_retry_errors=[]):
    for e in custom_retry_errors:
        if e in error:
            raise Exception(error)
    return {'error': error}