# Importer for data from csv
# Requires a schema
# Initialises a Sqlite3 db, imports a csv, inserts into the db
# simples
# (C)2023 DJM LZP

import pandas as pd
import sqlite3

CSVFILE = "projects.csv"
SCHEMA = "db_init.sql"

if __name__ == '__main__':
    csvdata = pd.read_csv(CSVFILE)

    database = sqlite3.connect("../db/sql3-database.sdb")

    # Initialise
    print("Reticulating Splines")
    schema = open("db_init.sql", mode="r")
    database.executescript(schema.read())

    # Load the data using executemany
    # It's in a dataframe, and we can discard the dataframe index as we don't need it
    database.executemany(
        "INSERT INTO projects VALUES(:number, :idea, :created, :done, :started_on, :stopped_on, :continuous, :links, :memoranda, :last_modified)",
        csvdata.itertuples(index=False))
    database.commit()

    database.close()
    print("0 OK 0:1")
