# FSSearch #

Search files indexed with FSCrawler.

This Version was tested with version 2.5 of FSCrawler, ElasticSearch
6.3.2 and Python 3.7. At least for Python other versions will
work. This program relies on the index structure FSCrawler 2.5
creates. Although this may change for other versions, not all of the
information is used, so it may work even if the index has another
format. For using this programm you must install FSCrawler and
ElasticSearch first and index your documents with FSCrawler.

# Howto use #
Install `requirements.txt`.
Just run `search.py` with a search term and submit the desired index with the --index flag.

# TODO #
Make `user_search` a variable of `SearchShell`. With this it can be used
to define a new print function. This will print the search along with
the results. It will be used in `do_print` and also in `do_search`, it may
also be used in `precmd`. `postcmd` is not good, as it will overwrite
everything.

Maybe another class for searching improves the situation. This can be
used separately for searching, parsing output, and even printing it.
With this extra class hopefully no globals are necessary anymore; the
state can be stored in the user interface class `SearchShell`.
