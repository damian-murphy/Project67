""" Data importer - imports a csv file in the expected format into a local sqlite3 db
    Does convert dates from D-M-YYYY HH:MM to python datetime objects
    Otherwise, imports as-is
    """
# Importer for data from csv
# Requires a schema
# Initialises a Sqlite3 db, imports a csv, inserts into the db
# simples
# (C)2023 DJM LZP
import argparse
import datetime
import sqlite3
import sys

import pandas as pd

# CSVFILE = "projects.csv"
SCHEMA_SQL = "db_init.sql"


def dt_from_str(string):
    """ Simple func to return datetime based on string input """
    if not pd.isna(string):
        return datetime.datetime.strptime(str(string), "%d/%m/%Y %H:%M")
    else:
        return string


def parse_cmdline():
    """
    Parse the command line options:
        -t type (database type, either sqlite3 or dynamodb)
        filename.csv (filename of csv data for import)
    :return:
    """
    # Parse any command line options.
    # Argparse seems nice.
    parser = \
        argparse.ArgumentParser(description="imports csv data into database")
    parser.add_argument("type", action="store",
                        help="select which back end to use - sqlite3 or dynamodb",
                        choices=['sqlite3', 'dynamodb'])
    parser.add_argument("filename", action="store",
                        help="filename to use for csv input")
    args = parser.parse_args()
    return args


def db_init(db_type):
    """ Initialise a database connection
    ::parameter db_type: either 'sqlite3' or 'dynamodb'
    ::returns connection object """

    if db_type == 'sqlite3':
        db_conn = sqlite3.connect("../db/sql3-database.sdb")  # pylint: disable=wrong-import-order
    elif db_type == 'dynamodb':
        db_conn = 'wibble'
    else:
        db_conn = None

    return db_conn


def setup_db(db_type, db_conn):
    """ Configure the schema
    ::parameter db_type: either 'sqlite3' or 'dynamodb'
    ::returns True on success """

    if db_type == 'sqlite3':
        schema = open(SCHEMA_SQL, mode="r", encoding="utf-8")  # pylint: disable=consider-using-with
        ret = db_conn.executescript(schema.read())
    elif db_type == 'dynamodb':
        ret = True
    else:
        # Something went wrong with the db_type parameter!
        ret = False

    return ret


if __name__ == '__main__':

    # See what we're asked to do
    options = parse_cmdline()
    CSVFILE = options.filename

    csvdata = pd.read_csv(CSVFILE)

    # Get a database connection
    try:
        database = db_init(options.type)
    except None as err:
        print("Error getting DB connection", err)
        sys.exit(2)

    # Initialise the database, mainly useful for creating a table in sql.
    # DynamoDB option requires a table already created
    print("Reticulating Splines")

    if not setup_db(options.type, database):
        print("Error initialising DB")
        sys.exit(2)
    # Ok, we're good so far

    # Load the data, fix the dates, insert a row at a time
    # It's in a dataframe, and we can discard the dataframe index as we don't need it
    count = 0
    for row in csvdata.itertuples(index=False):
        f_created = dt_from_str(row[2])
        f_done = dt_from_str(row[3])
        f_started_on = dt_from_str(row[4])
        f_stopped_on = dt_from_str(row[5])
        f_last_modified = dt_from_str(row[9])

        rowdata = (
            {"number": row[0], "idea": row[1], "created": f_created, "done": f_done,
             "started_on": f_started_on, "stopped_on": f_stopped_on, "continuous": row[6],
             "links": row[7], "memoranda": row[8], "last_modified": f_last_modified
             }
        )
        print(".", end='')
        count = count + 1
        database.execute("""INSERT INTO projects VALUES(:number, :idea, :created, :done,
                        :started_on, :stopped_on, :continuous, :links, :memoranda, 
                        :last_modified)""",
                         rowdata)
    database.commit()
    print("")
    print("Inserted " + str(count) + " rows into database.")
    database.close()
    print("0 OK 0:1")
