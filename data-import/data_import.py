# Importer for data from csv
# Requires a schema
# Initialises a Sqlite3 db, imports a csv, inserts into the db
# simples
# (C)2023 DJM LZP
import datetime
import pandas as pd
import sqlite3

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

    database = sqlite3.connect("../db/sql3-database.sdb")

    # Initialise
    print("Reticulating Splines")
    schema = open("db_init.sql", mode="r")
    database.executescript(schema.read())

    # Load the data using executemany
    # It's in a dataframe, and we can discard the dataframe index as we don't need it
    # database.executemany(
    #     "INSERT INTO projects VALUES(:number, :idea, :created, :done, :started_on, :stopped_on, :continuous, :links, :memoranda, :last_modified)",
    #     csvdata.itertuples(index=False))
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
        print(rowdata)
        database.execute("INSERT INTO projects VALUES(:number, :idea, :created, :done, :started_on, :stopped_on, :continuous, :links, :memoranda, :last_modified)",
                         rowdata)
    database.commit()

    database.close()
    print("0 OK 0:1")
