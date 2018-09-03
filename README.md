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
Just run `search.py` with a search term and submit the desired index
with the --index flag.

# TODO #
Provide possibility to search for an author explicitly. This may be
possible via a `bool` search with a `must_match` part for the author
and a `multi_match` part for the usual search string.

The author can be given directly as a command line parameter, more
important it is also necessary be able to search for the author in the
interactive part of the program. Therefore the search query has to be
parsed, for example it may or may not be a good idea to treat
everything after a single letter 'a' as the authors name.
