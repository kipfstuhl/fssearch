#!/usr/bin/env python3
from elasticsearch import Elasticsearch
import subprocess
import sys
import argparse

#from collections import namedtuple

parser = argparse.ArgumentParser(description='Search documents.')
parser.add_argument('query', nargs='*', type=str, help='The search term')
parser.add_argument('-a', '--author', nargs='+', type=str, help='Authors name')
args = parser.parse_args()

# Color = namedtuple('Color', ['purple', 'cyan', 'darkcyan', 'blue', 'green',
#                              'yellow', 'red', 'bold', 'underline', 'end'],
#                    defaults=['\033[95m', '\033[96m', '\033[36m', '\033[94m',
#                              '\033[92m', '\033[93m', '\033[91m', '\033[1m',
#                              '\033[4m', '\033[0m'])
# color = Color()
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

            self.blue   = subprocess.check_output("tput setaf 4".split()).decode()
            self.green  = subprocess.check_output("tput setaf 2".split()).decode()
            self.orange = subprocess.check_output("tput setaf 3".split()).decode()
            self.red    = subprocess.check_output("tput setaf 1".split()).decode()
            self.cyan   = subprocess.check_output("tput setaf 6".split()).decode()
            self.black  = subprocess.check_output("tput setaf 0".split()).decode()
            self.white  = subprocess.check_output("tput setaf 7".split()).decode()

            self.blue_bg   = subprocess.check_output("tput setab 4".split()).decode()
            self.green_bg  = subprocess.check_output("tput setab 2".split()).decode()
            self.orange_bg = subprocess.check_output("tput setab 3".split()).decode()
            self.red_bg    = subprocess.check_output("tput setab 1".split()).decode()
            self.cyan_bg   = subprocess.check_output("tput setab 6".split()).decode()
            self.black_bg  = subprocess.check_output("tput setab 0".split()).decode()
            self.white_bg  = subprocess.check_output("tput setab 7".split()).decode()
        except subprocess.CalledProcessError as e:
            self.bold = ""
            self.reset = ""

            self.blue   = ""
            self.green  = ""
            self.orange = ""
            self.red    = ""
            self.cyan   = ""
            self.black  = ""
            self.white  = ""

            self.blue_bg   = ""
            self.green_bg  = ""
            self.orange_bg = ""
            self.red_bg    = ""
            self.cyan_bg   = ""
            self.black_bg  = ""
            self.white_bg  = ""

_c = Colorcodes()


es = Elasticsearch(['localhost'])

def print_res(result, index=None):
    """Print one search result"""
    if index is not None:
        print(index, _c.bold+_c.blue+result['title']+_c.reset)
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

def print_result_list(results):
    """Print the complete list of search results"""
    for i, item in enumerate(results):
        print_res(item, i)
        print()

user_search = None
if len(args.query) > 1:
    user_search = ' '.join(args.query)
elif len(args.query) == 1:
    user_search = args.query[0]


def search(query):
    """Execute the query in elasticsearch."""
    
    req_body = {
        "query": {
            "multi_match" : {
                "query" : query,
                "fields" : ["content", "title", "author"],
                "fuzziness" : "AUTO"
            }
        },
        "sort": {
            "_score": {"order": "desc"}
        },
        "highlight": {
            # "pre_tags"  : [_c.bold + _c.blue], # for proper coloring use the direct api
            # "post_tags" : [_c.reset],
            
            # for proper coloring use the direct api
            "pre_tags"  : [ '<highlight>'  ],
            # shell escapes not working at beginning of string
            "post_tags" : [ '</highlight>' ],
            "order"     : "score",
            "number_of_fragments" : 1,
            "fields": {
                "content": {}
            }
        },
        "_source" : ['file.filename', 'path.real', 'meta.title',
                     'meta.raw.description']
    }
    
    res = es.search(index="test", body=req_body,
                     _source=['file.filename', 'path.real', 'meta.title',
                              'meta.raw.description'])
    return res

    
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


def parse_results(result):
    """Parse elasticsearch results.
    
    Parse a search result returned from elasticsearch client to return
    an array of dicts containing only the interesting parts.
    """

    interesting = []
    for item in result['hits']['hits']:
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
    return interesting


global interesting
interesting = []

if user_search is not None:
    res = search(user_search)
    interesting = parse_results(res)
    # print the interesting parts of the results
    print("Found", _c.bold + str(res['hits']['total']) + _c.reset, "results")
    print()
    print_result_list(interesting)


import cmd
class SearchShell(cmd.Cmd):
    intro  = 'Enter command. Type ? or help to list commands.\n'
    prompt = 'FSSearch: '

    clear_seq = subprocess.run(['tput', 'clear'], check=True, stdout=subprocess.PIPE).stdout
    clear_seq = clear_seq.decode()
    
    def do_exit(self, arg):
        'exit FSSearch'
        sys.exit()

    def do_q(self, arg):
        'exit FSSearch'
        self.do_exit(arg)

    def do_quit(self, arg):
        'exit FSSearch'
        self.do_exit(arg)

    def do_h(self, arg):
        'display help'
        self.do_help(arg)

    def do_open(self, arg):
        'Open the document of specified result'
        try:
            number = int(arg.split()[0])
            if (number < 0) or (number > len(interesting)):
                print("The number has to be in the range {} - {}"
                      .format(0, len(interesting)-1))
            else:
                # subprocess.run(['xdg-open', interesting[number]['path']])
                # use Popen to have a non-blocking call, i.e. don't
                # wait for xdg-open to return
                p = subprocess.Popen(['xdg-open', interesting[number]['path']])
        except ValueError:
            print("Not a number")

    def do_o(self, arg):
        'Open the document of specified result'
        self.do_open(arg)

    def do_search(self, arg):
        'Search for entered query'
        global interesting
        user_search = arg
        result = search(user_search)
        interesting = parse_results(result)
        # print(interesting)
        print_result_list(interesting)

    def do_print(self, arg):
        'Print results'
        global interesting
        if interesting:
            print('\033c', end='')
            print_result_list(interesting)
    
    def do_p(self, arg):
        'Print results'
        self.do_print(arg)
        
    def default(self, arg):
        if arg.isdecimal():
            self.do_open(arg)
        else:
            self.do_search(arg)

    def precmd(self, line):
        if line.split()[0] in ['help', '?', 'h']:
            print(self.clear_seq, end='')
        return line

    def postcmd(self, stop, line):
        if line.split()[0] in ['help', '?', 'h']:
            return stop
        global interesting
        if interesting:
            print(self.clear_seq, end='')
            print_result_list(interesting)

            

SearchShell().cmdloop()

    
# ask user for opening a search result
# give the possibility to choose more than one result
# question = "Type number to open, q to exit: "
# user_value = input(question)


# while True:
#     try:
#         want = int(user_value)
#         subprocess.run(["xdg-open", interesting[want]['path']])
#     except ValueError:
#         if user_value in ["q", "quit", "exit"]:
#             break
#             # sys.exit()
#         else:
#             print("Not a number")
            
#     user_value = input()

