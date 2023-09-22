
def make_query_dict(query:str):
    return {q.split('=')[0]:q.split('=')[1] for q in query.split('&')}