""" Module for loading parsed data from bitcointalk into PostgreSQL. """
import bitcointalk
import codecs
from datetime import date
from datetime import datetime
from datetime import time
from decimal import Decimal
import os
import psycopg2 as pg2
import psycopg2.extras as pg2ext
import random
import unittest

# Configuration variables
tables = {
    "board": "board",
    "member": "member",
    "message": "message",
    "topic": "topic"
}

# Pull in postgres configuration information
dbcFile = open(
    "{0}/.pgpass".format(os.path.dirname(os.path.abspath(__file__))),
    'r')
dbcRaw = dbcFile.readline().strip().split(':')
dbcParams = {
    'database': dbcRaw[2],
    'user': dbcRaw[3],
    'password': dbcRaw[4],
    'host': dbcRaw[0],
    'port': dbcRaw[1]
}
dbcFile.close()

# Connection variable
conn = None


def connect():
    """Connect to the database."""
    global conn
    if conn is not None:
        return conn
    else:
        conn = pg2.connect(**dbcParams)
        return conn


def cursor():
    """"Pull a cursor from the connection."""
    return connect().cursor()


def dictCursor():
    """"Pull a dictionary cursor from the connection."""
    return connect().cursor(cursor_factory=pg2ext.RealDictCursor)


def _insertSingle(datum, tableLabel):
    """Load a single row in to the database."""
    table = tables[tableLabel]
    cursor = dictCursor()
    dataFields = datum.keys()
    tableFields = []
    for dataField in dataFields:
        if dataField == "id":
            tableFields.append('sid')
        else:
            tableFields.append(dataField)
    cursor.execute("""
        DELETE FROM {0}
        WHERE sid = {1}""".format(table, datum['id']))
    cursor.execute("""INSERT INTO {0} ({1}) VALUES ({2})""".format(
        table,
        ",".join(tableFields),
        ",".join(["%({0})s".format(field) for field in dataFields])), datum)
    cursor.execute("COMMIT")


def _insertBatch(data, tableLabel):
    """Load a batch of rows to the database."""
    table = tables[tableLabel]
    cursor = dictCursor()
    dataFields = data[0].keys()
    tableFields = []
    for dataField in dataFields:
        if dataField == "id":
            tableFields.append('sid')
        else:
            tableFields.append(dataField)

    # Create staging table
    stagingTable = "{0}_{1}".format(
        table, str(int(pow(10, random.random()*10))).zfill(10))
    cursor.execute("""CREATE TABLE {0} (LIKE {1}
        )""".format(stagingTable, table))

    # Move data into staging table
    cursor.executemany("""INSERT INTO {0} ({1}) VALUES ({2})""".format(
        stagingTable,
        ",".join(tableFields),
        ",".join(["%({0})s".format(field) for field in dataFields])), data)

    # Delete old data from original table
    cursor.execute("""
        DELETE FROM {0} t
        USING {1} s
        WHERE t.sid = s.sid""".format(table, stagingTable))

    # Insert the new data into the target table
    cursor.execute("""
        INSERT INTO {0}
        (SELECT *
        FROM {1})""".format(table, stagingTable))

    # Drop the staging table
    cursor.execute("""
        DROP TABLE {0}""".format(stagingTable))

    # Commit the transaction
    cursor.execute("COMMIT")


def insertBoard(datum):
    """Load a single board."""
    _insertSingle(datum, 'board')


def insertMember(datum):
    """Load a single member."""
    _insertSingle(datum, 'member')


def insertMessages(data):
    """Load a batch of messages."""
    _insertBatch(data, 'message')


def insertTopic(datum):
    """Load a single topic."""
    _insertSingle(datum, 'topic')


def _selectSingle(datumId, tableLabel):
    """Pull a single datum from the DB."""
    cursor = dictCursor()
    table = tables[tableLabel]
    cursor.execute("""SELECT *
        FROM {0}
        WHERE sid = {1}""".format(table, datumId))
    rows = cursor.fetchall()
    if len(rows) == 0:
        raise Exception("Found 0 entries in DB for {0} ID {1}".format(
            tableLabel, datumId))
    elif len(rows) > 1:
        raise Exception("Found >1 entries in DB for {0} ID {1}".format(
            tableLabel, datumId))
    else:
        datum = rows[0]
        del datum['db_update_time']
        datum['id'] = datum.pop('sid')
        return datum


def _selectBatch(dataIds, tableLabel):
    """Pull batch of data from the DB."""
    cursor = dictCursor()
    table = tables[tableLabel]
    cursor.execute("""SELECT *
        FROM {0}
        WHERE sid IN ({1})
        ORDER BY sid""".format(
        table, ",".join([str(datumId) for datumId in dataIds])))
    rows = cursor.fetchall()
    if len(rows) != len(dataIds):
        raise Exception("Found {0} entries, but passed {1} IDs").format(
            len(rows), len(dataIds))
    else:
        for datum in rows:
            del datum['db_update_time']
            datum['id'] = datum.pop('sid')
        return rows


def selectBoard(datumId):
    """Pull a single board."""
    return _selectSingle(datumId, 'board')


def selectMember(datumId):
    """Pull a single member."""
    return _selectSingle(datumId, 'member')


def selectMessages(dataIds):
    """Pull multiple messages."""
    data = _selectBatch(dataIds, "message")
    # psycopg2 will not auto-decode UTF-8 strings to Unicode objects
    for datum in data:
        datum['content_no_html'] = codecs.decode(
            datum['content_no_html'], 'utf-8')
        datum['content_no_quote_no_html'] = codecs.decode(
            datum['content_no_quote_no_html'], 'utf-8')
    return data


def selectTopic(datumId):
    """Pull a single topic."""
    return _selectSingle(datumId, 'topic')


class PgTest(unittest.TestCase):

    """"Testing suite for pg module."""

    def setUp(self):
        """Setup tables for test."""
        # Swap and sub configuration variables
        global tables
        self.tablesOriginal = tables
        tables = {}
        for key, table in self.tablesOriginal.iteritems():
            tables[key] = "{0}_test".format(table)

        # Create test tables
        cur = cursor()
        for key, table in tables.iteritems():
            cur.execute("""CREATE TABLE IF NOT EXISTS
                {0} (LIKE {1} INCLUDING ALL)""".format(
                table, self.tablesOriginal[key]))
        cur.execute("""COMMIT""")

    def tearDown(self):
        """Teardown tables for test."""
        # Drop test tables
        global tables
        cur = cursor()
        for table in tables.values():
            cur.execute("""DROP TABLE IF EXISTS
                {0}""".format(table))
        cur.execute("""COMMIT""")

        # Undo swap / sub
        tables = self.tablesOriginal

    def testBoard(self):
        """Test insert and select board functions."""
        f = codecs.open("{0}/example/board_74.html".format(
            os.path.dirname(os.path.abspath(__file__))), 'r', 'utf-8')
        html = f.read()
        f.close()
        datum = bitcointalk.parseBoardPage(html)
        del datum["topic_ids"]
        insertBoard(datum)
        # Make sure a second insert doesn't cause problems
        insertBoard(datum)
        selectDatum = selectBoard(74)
        self.assertEqual(datum, selectDatum)

    def testMember(self):
        """Test insert and select member functions."""
        f = codecs.open("{0}/example/profile_12.html".format(
            os.path.dirname(os.path.abspath(__file__))), 'r', 'utf-8')
        html = f.read()
        f.close()
        todaysDate = date(2014, 7, 29)
        datum = bitcointalk.parseProfile(html, todaysDate)
        insertMember(datum)
        # Make sure a second insert doesn't cause problems
        insertMember(datum)
        selectDatum = selectMember(12)
        self.assertEqual(datum, selectDatum)

    def testMessages(self):
        """Test insert and select messages functions."""
        f = codecs.open("{0}/example/topic_602041.12400.html".format(
            os.path.dirname(os.path.abspath(__file__))), 'r', 'utf-8')
        html = f.read()
        f.close()
        data = bitcointalk.parseTopicPage(html)
        data = data['messages']
        insertMessages(data)
        # Make sure a second insert doesn't cause problems
        insertMessages(data)
        selectData = selectMessages(
            [
                8125509,
                8125667,
                8125970,
                8126348,
                8126542,
                8126615,
                8126655,
                8126666
            ])
        datum = data[0]
        self.assertEqual(data, selectData)

    def testTopic(self):
        """Test insert and select topic functions."""
        f = codecs.open("{0}/example/topic_14.html".format(
            os.path.dirname(os.path.abspath(__file__))), 'r', 'utf-8')
        html = f.read()
        f.close()
        datum = bitcointalk.parseTopicPage(html)
        del datum['messages']
        insertTopic(datum)
        # Make sure a second insert doesn't cause problems
        insertTopic(datum)
        selectDatum = selectTopic(14)
        self.assertEqual(datum, selectDatum)

if __name__ == "__main__":
    unittest.main()
