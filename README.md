bitcointalk-scraper
===================

Python-based scraper / crawler for members and messages on bitcointalk.org

Installation
=============

a) Make sure required python packages are installed

```
pip install cssselect lxml psycopg2 requests
```

b) Create tables in target PostgreSQL DB (see sql/)

c) Create .pgpass file in top-level of this directory containing connection info to the DB from previous step. Use the following format (9.1):

http://www.postgresql.org/docs/9.1/static/libpq-pgpass.html

d) Create "data" folder within the application folder, or change the _saveToFile method in memoizer.py to point to a different data directory.

Usage
=====

Main crawler will store information about all boards, members, messages, and topics falling within a user-defined range of topic IDs (as presented by bitcointalk.org). By default this range is between topics 1 and 50 - to change the range simple edit the "startTopicId" and "stopTopicId" variables within "scraper.py". When you're ready to start the crawler, simply run "python scrape_topics.py".

In the interest of avoiding heavy server load, the crawler, by default will wait an average of 5 seconds between requests to bitcointalk.org. To change this, simply edit the variable "interReqTime" in bitcointalk.py to the desired value.

The main crawler file included, "scrape_topics.py", is only one possible implementation of the crawler. The scraping interface, accessed through the memoizer sub-module, accepts a variety of commands and is smart enough to avoid scraping the same URL twice. Feel free to build your own custom crawler on top of this!
