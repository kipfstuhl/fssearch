#!/usr/bin/env python3
from elasticsearch import Elasticsearch
import subprocess
import sys
import argparse

parser = argparse.ArgumentParser(description="Search documents.")
parser.add_argument("query", nargs="*", type=str, help="The search term")
# parser.add_argument("-a", "--author", nargs="+", type=str, help="Authors name")
parser.add_argument("--index", default="_all", type=str,
                    help="Elasticsearch index in which the search is executed, "
                    "default is to use all indices")
args = parser.parse_args()

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
            self.bold      = subprocess.check_output("tput bold".split()).decode()
            self.reset     = subprocess.check_output("tput sgr0".split()).decode()

            self.blue      = subprocess.check_output("tput setaf 4".split()).decode()
            self.green     = subprocess.check_output("tput setaf 2".split()).decode()
            self.orange    = subprocess.check_output("tput setaf 3".split()).decode()
            self.red       = subprocess.check_output("tput setaf 1".split()).decode()
            self.cyan      = subprocess.check_output("tput setaf 6".split()).decode()
            self.black     = subprocess.check_output("tput setaf 0".split()).decode()
            self.white     = subprocess.check_output("tput setaf 7".split()).decode()

            self.blue_bg   = subprocess.check_output("tput setab 4".split()).decode()
            self.green_bg  = subprocess.check_output("tput setab 2".split()).decode()
            self.orange_bg = subprocess.check_output("tput setab 3".split()).decode()
            self.red_bg    = subprocess.check_output("tput setab 1".split()).decode()
            self.cyan_bg   = subprocess.check_output("tput setab 6".split()).decode()
            self.black_bg  = subprocess.check_output("tput setab 0".split()).decode()
            self.white_bg  = subprocess.check_output("tput setab 7".split()).decode()
        except subprocess.CalledProcessError as e:
            self.bold      = ""
            self.reset     = ""

            self.blue      = ""
            self.green     = ""
            self.orange    = ""
            self.red       = ""
            self.cyan      = ""
            self.black     = ""
            self.white     = ""

            self.blue_bg   = ""
            self.green_bg  = ""
            self.orange_bg = ""
            self.red_bg    = ""
            self.cyan_bg   = ""
            self.black_bg  = ""
            self.white_bg  = ""


_c = Colorcodes()

# ensure elasticsearch is running
# no check=True here, as systemctl returns a non zero code when it is not
# running, mostly 3
active = subprocess.run(
    ["systemctl", "is-active", "elasticsearch.service"], check=False, stdout=subprocess.PIPE
).returncode

if active != 0:
    print(
        _c.red + _c.bold + "ElasticSearch is currently not running.\n" + _c.reset
        + "Start it with systemctl:\n"
        + "systemctl start elasticsearch.service\n"
        + _c.bold + "Note: " + _c.reset
        + "it takes a while until the service is available. So a connection"
        + "error may occur at first attempt to retry.",
        end="\n\n",
    )
    sys.exit(1)
    # do not start the service, if started and the code is further
    # executed an error will occur
    # subprocess.run(["systemctl", "start", "elasticsearch.service"])


class Searcher:
    """Class for searching in the elasticsearch index"""

    def __init__(self, query=None, host=None, index=None):
        # query has to be passed for construction
        self.query = query or ""
        self.index = index or "_all"
        self.offset = 0
        self.es = Elasticsearch(hosts=host)
        self.interesting = self.search(query)

    def print_res(self, result, index=None):
        """Print one search result"""
        if index is not None:
            print("{:>3}".format(index)+ " " + _c.bold + _c.blue + result["title"] + _c.reset)
            if result["description"]:
                print(" "*4 + "Description:\t", result["description"])
            print(
                " "*4 +
                result["highlight"].replace("<highlight>", _c.blue).replace("</highlight>", _c.reset),
            )
            print(" "*4 + "Path: " +  result["path"])
        else:
            print("Title:\t\t", result["title"])
            if result["description"]:
                print("Description:\t", result["description"])
            print(result["highlight"])
            print("Path: ", result["path"])

    def print_result_list(self, results=None):
        """Print the complete list of search results"""
        if len(self.interesting) == 0:
            # if there are no results print this and end this mehtod,
            # otherwise it would be attempted to iterate over an empty
            # array
            print("No results available")
            return
        
        for i, item in enumerate(self.interesting, start=self.offset):
            self.print_res(item, i)
            print()

    def search(self, query, offset=0):
        """Executes the search and parses the results"""
        if query is not None:
            self.query = query
        self.offset = offset
        results = self.raw_search(query)
        self.interesting = self.parse_results(results)
        return self.interesting

    def raw_search(self, query=None):
        """Execute the query in elasticsearch."""

        # update query
        # if query is None:
        #     query = self.query
        if query is not None:
            self.query = query

        req_body = {
            "query": {
                "multi_match": {
                    "query":     self.query,
                    "fields":    ["content", "title", "author"],
                    "fuzziness": "AUTO",
                }
            },
            "sort": {"_score": {"order": "desc"}},
            "highlight": {
                # "pre_tags"  : [_c.bold + _c.blue], # for proper coloring use the direct api
                # "post_tags" : [_c.reset],
                # for proper coloring use the direct api
                # shell escapes not working at beginning of string, this can be
                # replaced later
                "pre_tags":  ["<highlight>"],
                "post_tags": ["</highlight>"],
                "order":     "score",
                "number_of_fragments": 1,
                "fields": {"content": {}},
            },
            "_source": ["file.filename", "path.real", "meta.title", "meta.raw.description"],
            "from":    self.offset
        }

        res = self.es.search(
            index=self.index,
            body=req_body,
            _source=["file.filename", "path.real", "meta.title", "meta.raw.description"],
        )
        return res

    def parse_results(self, result):
        """Parse elasticsearch results.

        Parse a search result returned from elasticsearch client to return
        an array of dicts containing only the interesting parts.
        """

        interesting = []
        for item in result["hits"]["hits"]:
            source = item["_source"]
            meta = source.get("meta")

            title     = "No title found"
            descr     = None
            os_path   = None
            highlight = None

            if meta is not None:
                title = meta.get("title") or "No title found"
                if meta.get("raw") is not None:
                    descr = meta.get("raw").get("description")

            path = source.get("path")
            if path is not None:
                os_path = path.get("real")

            highlight = " ".join(item["highlight"]["content"][0].split())

            temp = {
                "id":          item["_id"],
                "title":       title,
                "description": descr,
                "path":        os_path,
                "highlight":   highlight,
            }
            interesting.append(temp)
        self.interesting = interesting
        return interesting


import cmd


class SearchShell(cmd.Cmd):

    # some static variables, that are shared for all instances of this class
    # make sense, so these are not created inside __init__
    intro  = "Enter search term(s) or a command. Type ? or help to list commands."
    prompt = "FSSearch: "
    try:
        clear_seq = subprocess.run(["tput", "clear"], check=True, stdout=subprocess.PIPE).stdout
        clear_seq = clear_seq.decode()
    except Exception:
        clear_seq = ""

    def __init__(self, completekey="tab", stdin=None, stdout=None, query=None, index=None):
        super(SearchShell, self).__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        # the Searcher class handles None value for query, so just pass it here.
        self.s = Searcher(query=query, index=index)
        if query is not None:
            self.s.print_result_list()

    def do_exit(self, arg):
        "exit FSSearch"
        sys.exit()

    def do_q(self, arg):
        "exit FSSearch"
        self.do_exit(arg)

    def do_quit(self, arg):
        "exit FSSearch"
        self.do_exit(arg)

    def do_h(self, arg):
        "display help"
        self.do_help(arg)

    def do_open(self, arg):
        """Open the document of specified result
The numbers are displayed next to each serch result. The given number should be the displayed number or the last digit, i.e. 1 works also for result number 11.
"""
        try:
            number = int(arg.split()[0]) % 10 # 10 is the maximum list length
            if (number < 0) or (number > len(self.s.interesting)-1):
                if len(self.s.interesting) == 0:
                    print("You have to execute a search first.")
                # this error statement is somewhat outdated, to be
                # correct the number has to be in this range modulo 10
                print(_c.bold +
                      "The number has to be in the range {} - {}".format(0+self.s.offset, len(self.s.interesting) - 1 + self.s.offset) +
                      _c.reset)
            else:
                # use Popen to have a non-blocking call, i.e. don't
                # wait for xdg-open to return
                p = subprocess.Popen(["xdg-open", self.s.interesting[number]["path"]])
        except ValueError:
            print("Not a number")
        except IndexError:
            print("Specify a number for the result to open")

    def do_o(self, arg):
        "Open the document of specified result\nSee documentation for open."
        self.do_open(arg)

    def do_search(self, arg):
        "Search for entered query"
        global interesting
        user_search = arg
        self.s.query = user_search
        self.s.search(user_search)
        print(self.clear_seq, end="")
        if user_search is not None:
            print("Current search: " + _c.bold + user_search + _c.reset, end="\n\n")
            self.s.print_result_list()

    def do_s(self, arg):
        "Search for entered query"
        self.do_search(arg)

    def do_print(self, arg):
        "Print results"
        # Nothing to do here. Bevore every command is executed the
        # reult list is printed in function precmd.
        pass

    def do_p(self, arg):
        "Print results"
        self.do_print(arg)

    def do_forward(self, arg):
        "Scroll down results"
        old_offset = self.s.offset
        self.s.search(self.s.query, offset = old_offset + 10)
        # new print necessary, otherwise the old list is shown because
        # of precmd printing
        print(self.clear_seq, end="")
        print("Current search: " + _c.bold + self.s.query + _c.reset, end="\n\n")
        self.s.print_result_list()

    def do_f(self,arg):
        "Scroll down results"
        self.do_forward(arg)

    def do_back(self, arg):
        "Scroll up results"
        old_offset = self.s.offset
        new_offset = max(old_offset - 10, 0)
        self.s.search(self.s.query, offset =new_offset)
        # new print necessary, otherwise the old list is shown because
        # of precmd printing
        print(self.clear_seq, end="")
        print("Current search: " + _c.bold + self.s.query + _c.reset, end="\n\n")
        self.s.print_result_list()

    def do_b(self,arg):
        "Scroll up results"
        self.do_back(arg)

    def default(self, arg):
        if arg.isdecimal():
            self.do_open(arg)
        else:
            self.do_search(arg)

    def precmd(self, line):
        print(self.clear_seq, end="")
        if line.split() and line.split()[0] in ["help", "?", "h"]:
            # early return without printing results
            return line
        if self.s.query not in [None, ""]:
            print("Current search: " + _c.bold + self.s.query + _c.reset, end="\n\n")
        self.s.print_result_list()
        return line

    def postcmd(self, stop, line):
        print(self.intro)
        return stop


user_search = None
if len(args.query) > 1:
    user_search = " ".join(args.query)
elif len(args.query) == 1:
    user_search = args.query[0]

SearchShell(query=user_search, index=args.index).cmdloop()
