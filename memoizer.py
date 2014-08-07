""" Module for loading parsed data from bitcointalk into PostgreSQL. """
import bitcointalk
import codecs
from datetime import datetime
import os
import pg
import time
import unittest

memo = {
    'boards': set(),
    'members': set(),
    'topics': set()
}


def _insertTopicPage(data):
    """Insert data as topic and messages and splice off messages."""
    pg.insertMessages(data.pop('messages'))
    pg.insertTopic(data)


entityFunctions = {
    'board': {
        'requestor': bitcointalk.requestBoard,
        'parser': bitcointalk.parseBoard,
        'inserter': pg.insertBoard,
        'selector': pg.selectBoard
    },
    'member': {
        'requestor': bitcointalk.requestProfile,
        'parser': bitcointalk.parseProfile,
        'inserter': pg.insertMember,
        'selector': pg.selectMember
    },
    'topic': {
        'requestor': bitcointalk.requestTopicPage,
        'parser': bitcointalk.parseTopicPage,
        'inserter': _insertTopicPage,
        'selector': pg.selectTopic
    }
}


def _saveToFile(html, fileType, fileDescriptor):
    """Save given entity to a file."""
    f = codecs.open("{0}/data/{1}_{2}_{3}.html".format(
        os.path.dirname(os.path.abspath(__file__)),
        fileType, fileDescriptor,
        int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())),
        'w', 'utf-8')
    f.write(html)
    f.close()


def remember():
    """Remember what's already in the database to avoid re-scraping."""
    global memo
    cursor = pg.cursor()
    for key in memo.keys():
        cursor.execute("SELECT sid FROM {0}".format(pg.tables[key[:-1]]))
        rows = cursor.fetchall()
        for row in rows:
            memo[key].add(row[0])
    return True


def _scrape(entity, entityId):
    global memo
    global entityFunctions
    entityPlural = "{0}s".format(entity)
    if entityId in memo[entityPlural]:
        return entityFunctions[entity]['selector'](entityId)
    else:
        html = entityFunctions[entity]['requestor'](entityId)
        _saveToFile(html, entity, entityId)
        datum = entityFunctions[entity]['parser'](html)
        entityFunctions[entity]['inserter'](datum)
        memo[entityPlural].add(entityId)
        return datum


def scrapeBoard(boardId):
    """Scrape information on the specified board."""
    return _scrape('board', boardId)


def scrapeMember(memberId):
    """Scrape the profile of the specified member."""
    return _scrape('member', memberId)


def scrapeMessages(topicId, pageNum):
    """Scrape all messages on the specified topic, page combination."""
    """CAVEAT: Messages are not memoized."""
    offset = (pageNum-1)*20
    html = bitcointalk.requestTopicPage(topicId, offset)
    _saveToFile(html, "topicpage", "{0}.{1}".format(topicId, offset))
    data = bitcointalk.parseTopicPage(html)
    data = data['messages']
    pg.insertMessages(data)
    return data


def scrapeTopic(topicId):
    """Scrape information on the specified topic."""
    return _scrape('topic', topicId)


class MemoizerTest(unittest.TestCase):

    """"Testing suite for memoizer module."""

    def setUp(self):
        """Setup tables and memo for test."""
        # Swap and sub tables
        self.tablesOriginal = pg.tables
        pg.tables = {}
        for key, table in self.tablesOriginal.iteritems():
            pg.tables[key] = "{0}_test".format(table)

        # Create test tables
        cur = pg.cursor()
        for key, table in pg.tables.iteritems():
            cur.execute("""CREATE TABLE IF NOT EXISTS
                {0} (LIKE {1} INCLUDING ALL)""".format(
                table, self.tablesOriginal[key]))
        cur.execute("""COMMIT""")

        # Reset memo
        global memo
        self.memoOriginal = memo
        memo = {
            'boards': set(),
            'members': set(),
            'topics': set()
        }

    def tearDown(self):
        """Teardown tables for test and restore memo."""
        # Drop test tables
        cur = pg.cursor()
        for table in pg.tables.values():
            cur.execute("""DROP TABLE IF EXISTS
                {0}""".format(table))
        cur.execute("""COMMIT""")

        # Undo swap / sub of tables
        pg.tables = self.tablesOriginal

        # Undo swap / sub of memo
        global memo
        memo = self.memoOriginal

    def testScrapeBoard(self):
        """Test scrapeBoard function."""
        countRequestedStart = bitcointalk.countRequested
        datumFirst = scrapeBoard(74)
        datumSecond = scrapeBoard(74)
        countRequestedEnd = bitcointalk.countRequested
        self.assertEqual(countRequestedEnd - countRequestedStart, 1)
        datumExpected = {
            'id': 74,
            'name': 'Legal',
            'container': 'Bitcoin',
            'parent': 1
        }
        self.assertEqual(datumExpected, datumFirst)
        self.assertEqual(datumExpected, datumSecond)
        self.assertEqual(datumFirst, datumSecond)

    def testScrapeMember(self):
        """Test scrapeMember function."""
        countRequestedStart = bitcointalk.countRequested
        datumFirst = scrapeMember(12)
        datumSecond = scrapeMember(12)
        countRequestedEnd = bitcointalk.countRequested
        self.assertEqual(countRequestedEnd - countRequestedStart, 1)
        datumExpected = {
            'id': 12,
            'name': 'nanaimogold',
            'position': 'Sr. Member',
            'date_registered': datetime(2009, 12, 9, 19, 23, 55),
            'last_active': datetime(2014, 6, 3, 0, 38, 1),
            'email': 'hidden',
            'website_name': 'Nanaimo Gold Digital Currency Exchange',
            'website_link': 'https://www.nanaimogold.com/',
            'bitcoin_address': None,
            'other_contact_info': None,
            'signature': '<a href="https://www.nanaimogold.com/" ' +
            'target="_blank">https://www.nanaimogold.com/</a> ' +
            '- World\'s first bitcoin exchange service'
        }
        self.assertEqual(datumExpected, datumFirst)
        self.assertEqual(datumExpected, datumSecond)
        self.assertEqual(datumFirst, datumSecond)

    def testScrapeTopic(self):
        """Test scrapeTopic function."""
        countRequestedStart = bitcointalk.countRequested
        datumFirst = scrapeTopic(14)
        datumSecond = scrapeTopic(14)
        countRequestedEnd = bitcointalk.countRequested
        self.assertEqual(countRequestedEnd - countRequestedStart, 1)
        datumExpected = {
            'id': 14,
            'name': 'Break on the supply\'s increase',
            'board': 7,
            'num_pages': 1
        }
        self.assertEqual(datumFirst['count_read'], datumSecond['count_read'])
        self.assertEqual(datumFirst.pop('count_read') > 3057, True)
        self.assertEqual(datumSecond.pop('count_read') > 3057, True)
        self.assertEqual(datumExpected, datumFirst)
        self.assertEqual(datumExpected, datumSecond)
        self.assertEqual(datumFirst, datumSecond)

        # Make sure we can pull in the associated messages without error
        pg.selectMessages([53, 56])

    def testScrapeMessages(self):
        """Test scrapeMessages function."""
        countRequestedStart = bitcointalk.countRequested
        data = scrapeMessages(14, 1)
        countRequestedEnd = bitcointalk.countRequested
        self.assertEqual(countRequestedEnd - countRequestedStart, 1)
        self.assertEqual(len(data), 2)

        # Make sure we can pull in the associated messages without error
        pg.selectMessages([53, 56])

    def testRemember(self):
        """Test remember function."""
        scrapeBoard(74)
        scrapeMember(12)
        scrapeTopic(14)
        global memo
        memo = {
            'boards': set(),
            'members': set(),
            'topics': set()
        }
        remember()
        expectedMemo = {
            'boards': set([74]),
            'members': set([12]),
            'topics': set([14])
        }
        self.assertEqual(memo, expectedMemo)


if __name__ == "__main__":
    unittest.main()
