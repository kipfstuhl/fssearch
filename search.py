from elasticsearch import Elasticsearch
import subprocess
import sys


Color = namedtuple('Color', ['purple', 'cyan', 'darkcyan', 'blue', 'green',
                             'yellow', 'red', 'bold', 'underline', 'end'],
                   defaults=['\033[95m', '\033[96m', '\033[36m', '\033[94m',
                             '\033[92m', '\033[93m', '\033[91m', '\033[1m',
                             '\033[4m', '\033[0m'])
color = Color()
# PURPLE    = '\033[95m'
# CYAN      = '\033[96m'
# DARKCYAN  = '\033[36m'
# BLUE      = '\033[94m'
# GREEN     = '\033[92m'
# YELLOW    = '\033[93m'
# RED       = '\033[91m'
# BOLD      = '\033[1m'
# UNDERLINE = '\033[4m'
# END       = '\033[0m'

es = Elasticsearch(['localhost'])

def print_res(result, index=None):
    if index is not None:
        print(i,"Title:\t", result['title'])
        print("  Description:\t", result['description'])
        print("  Path: ", result['path'])
        print(" ", result['highlight'])
    else:
        print("Title:\t\t", result['title'])
        print("Description:\t", result['description'])
        print("Path: ", result['path'])
        print(result['highlight'])


user_search = input("Search term: ")

req_body = {
    "query": {
        "multi_match" : {
            "query" : user_search,
            "fields" : ["content", "title", "author"],
            "fuzziness" : "AUTO"
        }
    },
    "sort": {
        "_score": {"order": "desc"}
    },
    "highlight": {
        "pre_tags"  : [color.bold],
        "post_tags" : [color.end],
        "order"     : "score",
        "number_of_fragments" : 1,
        "fields": {
            "content": {}
        }
    }
}

res2 = es.search(index="test", body=req_body, _source=['file.filename', 'path.real', 'meta.title', 'meta.raw.description'])

# parse results
interesting = []
for item in res2['hits']['hits']:
    source = item['_source']
    meta = source.get('meta')

    title     = None
    descr     = None
    os_path   = None
    highlight = None
    if meta is not None:
        title = meta.get('title')
        if meta.get('raw') is not None:
            descr = meta.get('raw').get('description')
    
    path  = source.get('path')    
    if path is not None:
        os_path = path.get('real')
    highlight = str(item['highlight']['content'][0]).replace('\n', '')
    temp = {
        'id' :          item['_id'],
        'title' :       title,
        'description' : descr,
        'path' :        os_path,
        'highlight' :   highlight
    }
    interesting.append(temp)
    
# print the interesting parts of the results
print("Found", color.bold + str(res2['hits']['total']) + color.end, "results")
print()
for i, item in enumerate(interesting):
    print_res(item, i)
    print()

# ask user for opening a search result
# give the possibility to choose more than one result
while True:
    user_value = input("Type number to open, q to exit\n")
    try:
        want = int(user_value)
    except ValueError:
        if user_value == "q":
            sys.exit()
        else:
            print("Not a number")
            
    subprocess.call(["xdg-open", interesting[want]['path']])
            
