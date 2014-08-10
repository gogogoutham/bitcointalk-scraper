""" Core scraper for bitcointalk.org. """
import bitcointalk
import logging
import memoizer
import os
import sys
import traceback

startTopicId = 1
stopTopicId = 50

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')

# Make sure we don't rescrape information already in the DB
memoizer.remember()

for topicId in range(startTopicId, stopTopicId+1):
    logging.info(">Starting scrape of topic ID {0}...".format(topicId))
    try:
        topic = memoizer.scrapeTopic(topicId)
    except Exception as e:
        print '-'*60
        print "Could not request URL for topic {0}:".format(topicId)
        print traceback.format_exc()
        print '-'*60
        logging.info(">Could not request URL for topic {0}:".format(topicId))
        continue
    logging.info(">Scraping related board...")
    memoizer.scrapeBoard(topic['board'])
    logging.info(">Found {0} message pages...".format(
        topic['num_pages'] - 1))
    for pageNum in range(1, topic['num_pages'] + 1):
        logging.info(">>Scraping page {0}...".format(pageNum))
        messages = memoizer.scrapeMessages(topic['id'], pageNum)
        for message in messages:
            if message['member'] > 0:
                memoizer.scrapeMember(message['member'])
        logging.info(">>Done with page {0}.".format(pageNum))
    logging.info(">Done scraping topic ID {0}.".format(topicId))

logging.info("All done.")
logging.info("Made {0} requests in total.".format(bitcointalk.countRequested))
