""" Data importer - imports a csv file in the expected format into a local sqlite3 db
    Does convert dates from D-M-YYYY HH:MM to python datetime objects
    Otherwise, imports as-is
    """
# Importer for data from csv
# Requires a schema
# Initialises a Sqlite3 db, imports a csv, inserts into the db
# simples
# (C)2023 DJM LZP
import datetime
import sqlite3
import pandas as pd

CSVFILE = "projects.csv"
SCHEMA = "db_init.sql"

def dt_from_str(string):
    """ Simple func to return datetime based on string input """
    if not pd.isna(string):
        return datetime.datetime.strptime(str(string), "%d/%m/%Y %H:%M")
    else:
        return string

if __name__ == '__main__':
    csvdata = pd.read_csv(CSVFILE)

    database = sqlite3.connect("../db/sql3-database.sdb")  # pylint: disable=wrong-import-order

    # Initialise
    print("Reticulating Splines")
    schema = open("db_init.sql", mode="r", encoding="utf-8")  # pylint: disable=consider-using-with
    database.executescript(schema.read())

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
        count = count+1
        database.execute("""INSERT INTO projects VALUES(:number, :idea, :created, :done,
                        :started_on, :stopped_on, :continuous, :links, :memoranda, 
                        :last_modified)""",
                         rowdata)
    database.commit()
    print("")
    print("Inserted " + str(count) + " rows into database.")
    database.close()
    print("0 OK 0:1")
