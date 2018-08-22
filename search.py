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

print(args.query)
if args.author:
    print(' '.join(args.author))


es = Elasticsearch(['localhost'])

def print_res(result, index=None):
    if index is not None:
        print(i,"Title:\t", result['title'])
        print("  Description:\t", result['description'])
        print("  Path: ", result['path'])
    else:
        print("Title:\t\t", result['title'])
        print("Description:\t", result['description'])
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

    title   = None
    descr   = None
    os_path = None
    if meta is not None:
        title = meta.get('title')
        if meta.get('raw') is not None:
            descr = meta.get('raw').get('description')
    
    path  = source.get('path')    
    if path is not None:
        os_path = path.get('real')
    
    try:
        temp = {
            'id' :          item['_id'],
            'title' :       title,
            'description' : descr,
            'path' :        os_path
        }
        interesting.append(temp)
    except Exception as e:
        pass

# print the interesting parts of the results
print("Found", res2['hits']['total'], "results")
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
            
