""" Database.py:
    Contains database storage functions. These functions can be a wrapper around
    whatever storage mechanism we want to use.
    Currently, it's sqlite3 stored locally.
    """
# Let's use SQL-Lite for now, we can always change this up later if needed

import sqlite3
import boto3
from flask import current_app, g


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        if current_app.config['DBTYPE'] == "sqlite3":
            g.db = sqlite3.connect("db/sql3-database.sdb")
            g.db.row_factory = sqlite3.Row
        elif current_app.config['DBTYPE'] == "dynamodb":
            conn = boto3.resource('dynamodb', region_name='eu-west-1')
            g.db = conn.Table(current_app.config['TABLENAME'])  # return table object for dynamodb
        else:
            g.db = None  # ruh-roh raggy!

    return g.db


def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    if current_app.config['DBTYPE'] == "sqlite3":
        db = g.pop("db", None)

        if db is not e:
            db.close()
    # Otherwise, do nothing, dynamodb has no close as such


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
