#!/usr/bin/env python3
from elasticsearch import Elasticsearch
import subprocess
import sys

from collections import namedtuple
import argparse

parser = argparse.ArgumentParser(description='Search documents.')
parser.add_argument('query', nargs='+', type=str, help='The search term')
parser.add_argument('-a', '--author', nargs='+', type=str, help='Authors name')
args = parser.parse_args()

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


class Colorcodes(object):
    def __init__(self):
        try:
            self.bold = subprocess.check_output("tput bold".split()).decode()
            self.reset = subprocess.check_output("tput sgr0".split()).decode()

            self.blue = subprocess.check_output("tput setaf 4".split()).decode()
            self.green = subprocess.check_output("tput setaf 2".split()).decode()
            self.orange = subprocess.check_output("tput setaf 3".split()).decode()
            self.red = subprocess.check_output("tput setaf 1".split()).decode()
        except subprocess.CalledProcessError as e:
            self.bold = ""
            self.reset = ""

            self.blue = ""
            self.green = ""
            self.orange = ""
            self.red = ""

_c = Colorcodes()


es = Elasticsearch(['localhost'])

def print_res(result, index=None):
    if index is not None:
        print(i, _c.bold+_c.blue+result['title']+_c.reset)
        if result['description']:
            print("  Description:\t", result['description'])
        print(" ",
              result['highlight'].replace('<highlight>', _c.blue).replace('</highlight>', _c.reset))
        print("  Path: ", result['path'])
    else:
        print("Title:\t\t", result['title'])
        if result['description']:
            print("Description:\t", result['description'])
        print(result['highlight'])
        print("Path: ", result['path'])


user_search = None
if len(args.query) > 1:
    user_search = ' '.join(args.query)
else:
    user_search = args.query[0]

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
        # "pre_tags"  : [color.bold+color.blue],
        # "post_tags" : [color.end],
        # "pre_tags"  : [_c.bold + _c.blue], # for proper coloring use the direct api
        # "post_tags" : [_c.reset],
        "pre_tags"  : [ '<highlight>'  ], # for proper coloring use the direct api
        "post_tags" : [ '</highlight>' ], # shell escapes not working at beginning of string
        "order"     : "score",
        "number_of_fragments" : 1,
        "fields": {
            "content": {}
        }
    },
    "_source" : ['file.filename', 'path.real', 'meta.title', 'meta.raw.description']
}

res2 = es.search(index="test", body=req_body, _source=['file.filename', 'path.real', 'meta.title', 'meta.raw.description'])

# import urllib.request
# import json

# # decoder = json.JSONDecoder(strict=False)
# body = json.dumps(req_body).encode('utf-8')
# req = urllib.request.Request("http://localhost:9200/test/_search", data=body,
#               headers={"Content-Type" : "application/json"}, method="GET")

# with urllib.request.urlopen(req) as x:
#     res_string = x.read()
#     res_json = json.loads(res_string, strict=False)
#     print(x.status)

# res2 = res_json


# parse results
interesting = []
for item in res2['hits']['hits']:
    source = item['_source']
    meta = source.get('meta')

    title     = 'No title found'
    descr     = None
    os_path   = None
    highlight = None

    if meta is not None:
        title = meta.get('title') or 'No title found'
        if meta.get('raw') is not None:
            descr = meta.get('raw').get('description')
    
    path  = source.get('path')
    if path is not None:
        os_path = path.get('real')

    highlight = item['highlight']['content'][0].replace('\n', ' ')

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
question = "Type number to open, q to exit: "
user_value = input(question)


while True:
    try:
        want = int(user_value)
        subprocess.call(["xdg-open", interesting[want]['path']])
    except ValueError:
        if user_value.decode() in ["q", "quit", "exit"]:
            break
            # sys.exit()
        else:
            print("Not a number")
            
    user_value = input()

