# news-similarity

Github project with all code needed for the final degree project "News similarity with Natural Language Processing". 
It tries to stablish a distance between the content of politics news articles, so that a network of similarities can be built.

This project has been organised in four Python libraries, detailed here:
* newsparser: defines classes Feed and Entry to extract entries from a RSS feed, 
saving all the necessary metadata and the article text in the central database.
* newsfilter: defines classes and methods to filter those entries 
that should not be considered in the system, such as entries with a broken link, 
that had no title, that had no meaningful content, etc.
* newstagger: defines a Flask HTTP server and its pages to allow an easy creation 
of a tagged dataset for the creation of the system.
* newsbreaker: defines functions and classes that inherit from the Entry class 
in newsparser and allow for an easy access to its content, its counters of words, 
its what/who/where vectors and some methods to compute the distance between two of them.

All Python code is Python 3.

For more details on this system, check the project report: // TODO: Upload file and link this
