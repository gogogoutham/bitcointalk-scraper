""" Core scraper for bitcointalk.org. """
import bitcointalk
import logging
import memoizer
import os
import sys
import traceback

boardId = 74

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')

# Make sure we don't rescrape information already in the DB
memoizer.remember()

logging.info("Beginning scrape of board ID...".format(boardId))
board = memoizer.scrapeBoard(boardId)
logging.info("Found {0} topic pages in board...".format(
    board['num_pages']))
for boardPageNum in range(1, board['num_pages'] + 1):
    logging.info(">Scraping page {0}...".format(boardPageNum))
    topicIds = memoizer.scrapeTopicIds(boardId, boardPageNum)
    for topicId in topicIds:
        logging.info(">>Starting scrape of topic ID {0}...".format(topicId))
        # try:
        #     topic = memoizer.scrapeTopic(topicId)
        # except Exception as e:
        #     print '-'*60
        #     print "Could not request URL for topic {0}:".format(topicId)
        #     print traceback.format_exc()
        #     print '-'*60
        #     logging.info(">>Could not request URL for topic {0}:".format(
        #         topicId))
        #     continue
        # logging.info(">>Found {0} message pages in topic...".format(
        #     topic['num_pages']))
        # for topicPageNum in range(1, topic['num_pages'] + 1):
        #     logging.info(">>>Scraping page {0}...".format(topicPageNum))
        #     messages = memoizer.scrapeMessages(topic['id'], topicPageNum)
        #     for message in messages:
        #         if message['member'] > 0:
        #             memoizer.scrapeMember(message['member'])
        #     logging.info(">>>Done with page {0}.".format(topicPageNum))
        logging.info(">>Done scraping topic ID {0}.".format(topicId))
    logging.info(">Done with page {0}.".format(boardPageNum))

logging.info("All done.")
logging.info("Made {0} requests in total.".format(bitcointalk.countRequested))
