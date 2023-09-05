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

import botocore
import yaml
import boto3
import pandas as pd

# CSVFILE = "projects.csv"
SCHEMA_SQL = "db_init.sql"
SCHEMA_YAML = "db_init.yaml"


def dt_from_str(string):
    """ Simple func to return ISO formatted date based on string input
    Expects format "%d/%m/%Y %H:%M" as that was in the original input,
    returns format "%Y-%m-%dT%H:%M"
    If NULL or NAN is passed, we return None type
    We will interpret this as 'Not Set' for key-value stores, and as NaN for SQL stores
    """
    if not pd.isna(string):
        dt_tmp = datetime.datetime.strptime(str(string), "%d/%m/%Y %H:%M")
        return datetime.datetime.strftime(dt_tmp, "%Y-%m-%dT%H:%M")
    else:
        return None


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
        db_conn = boto3.resource('dynamodb', region_name='eu-west-1')
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
        # Load the yaml config file for the key type and attributes
        try:
            schema = yaml.safe_load(open(SCHEMA_YAML))
        except (yaml.YAMLError, IOError) as err:
            print("R Tape Loading Error, ", err)
            return False

        # Create table unless exists, in which case this thing throws shapes
        try:
            table = db_conn.create_table(TableName=schema['ddb_tablename'], KeySchema=schema['ddb_keyschema'],
                                         AttributeDefinitions=schema['ddb_attribdefs'],
                                         ProvisionedThroughput={
                                            'ReadCapacityUnits': 1,
                                            'WriteCapacityUnits': 1
                                            }
                                         )
        except db_conn.meta.client.exceptions.ResourceInUseException as err:
            print("Oh dear, the table already exists!")
            print("Will now delete it first")

            # Let's just re-use the existing table and update it to be sure.
            # Fingers crossed we're not blowing something away here, so make sure you've setup the right
            # resources in AWS or otherwise ka-blooey

            # Get the client connection object first
            table = db_conn.meta.client

            # Now we can delete it and re-create
            table.delete_table(TableName=schema['ddb_tablename'])

            # If we jump ahead now, the table may not yet be deleted and we'll end up having to redo from start
            # So use these waiter processes.
            print("Waiting for table deletion to be confirmed...", end='')
            waiter = table.get_waiter('table_not_exists')
            waiter.wait(TableName=schema['ddb_tablename'])
            print("done")

            print("Re-creating table...", end='')
            table = db_conn.create_table(TableName=schema['ddb_tablename'], KeySchema=schema['ddb_keyschema'],
                                         AttributeDefinitions=schema['ddb_attribdefs'],
                                         ProvisionedThroughput={
                                             'ReadCapacityUnits': 1,
                                             'WriteCapacityUnits': 1
                                         }
                                         )

        table.wait_until_exists()
        print("done")
        # if empty, this will return 0
        if table.item_count == 0:
            ret = table  # for dynamodb, we want to return the table object, so we can use it for inserts later
        else:
            ret = False  # ruh-roh raggy!
    else:
        # Something went wrong with the db_type parameter!
        ret = False

    return ret


def db_insert(db_type, db_conn, data):
    """ Insert data into database
    ::parameter db_type: either sqlite3 or dynamodb
    ::parameter db_conn: database connection string (sqlite3) or table object (dynamodb)
    ::parameter data: named tuple with a single row from the csvfile
    ::returns True on success """

    if db_type == 'sqlite3':
        ret = db_conn.execute("""INSERT INTO projects VALUES(:number, :idea, :created, :done,
                              :started_on, :stopped_on, :continuous, :links, :memoranda, 
                              :last_modified)""",
                              data)
        db_conn.commit()
    elif db_type == 'dynamodb':
        # we've got the table object as database so carry on
        # Bonus points - we have the data in the right structure already.
        ret = table.put_item(Item=data)
    else:
        # Something went wrong with the db_type parameter!
        ret = False

    return ret


def db_close(db_type, db_conn):
    """ Close the open database connection
    ::parameter db_type: either sqlite3 or dynamodb
    ::parameter db_conn: connection object
    ::returns True on success """

    if db_type == 'sqlite3':
        db_conn.close()
        ret = True
    elif db_type == 'dynamodb':
        ret = True  # nothing to do here
    else:
        ret = False  # ruh-roh

    return ret


def strip_nan(string):
    """ Convert NaN to 'NA'
    For sqlite3, we can store NaN and deal with that,
    but for dynamodb, we will have a missing attribute instead. This is to get around
    not being able to store NaN values """
    if not pd.isna(string):
        return string
    # otherwise
    return "NA"

def check_is_null(item):
    """ Check for null, nan, None type
    ::parameter item to test
    ::returns True if we see a None, NaN or NULL value, False otherwise """
    if pd.isna(item):
        return True
    elif item is None:
        return True

    return False


if __name__ == '__main__':

    # See what we're asked to do
    options = parse_cmdline()
    CSVFILE = options.filename

    csvdata = pd.read_csv(CSVFILE)

    # Get a database connection
    database = db_init(options.type)
    if database is None:
        print("Error getting DB connection!")
        sys.exit(2)

    # Initialise the database, mainly useful for creating a table in sql.
    # DynamoDB option requires a table already created
    print("Initialising a database of type " + options.type + ", and reticulating splines.")

    # need the return value here, the dynamodb table object
    # for sqlite3, this will be 'true' and can be discarded
    table = setup_db(options.type, database)
    if not table:
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

        if options.type == 'sqlite3':
            rowdata = (
                {"number": row[0], "idea": row[1], "created": f_created, "done": f_done,
                 "started_on": f_started_on, "stopped_on": f_stopped_on, "continuous": row[6],
                 "links": row[7], "memoranda": row[8], "last_modified": f_last_modified
                 }
            )
        else:
            # Must be dynamodb so
            # We need to remove any NaN/Null/None values
            itemlist = {
                    "number": row[0], "idea": row[1], "created": f_created, "done": f_done,
                    "started_on": f_started_on, "stopped_on": f_stopped_on, "continuous": row[6],
                    "links": row[7], "memoranda": row[8], "last_modified": f_last_modified
                    }

            rowdata = {}
            for item in itemlist:
                if not check_is_null(itemlist[item]):
                    rowdata.update({item: itemlist[item]})
            print(rowdata)

        print(".", end='')
        count = count + 1
        if options.type == 'dynamodb':
            # set param to table object for dynamodb
            database = table

        if not db_insert(options.type, database, rowdata):
            print("Error inserting values!")
            sys.exit(2)

    print("")
    print("Inserted " + str(count) + " rows into database.")
    if db_close(options.type, database):
        print("DB Connection closed.")
    else:
        print("Error closing db!")
    print("0 OK 0:1")
