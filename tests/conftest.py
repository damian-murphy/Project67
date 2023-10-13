# Tests for the p67 app
#

import pytest
from projects import app as my_app


@pytest.fixture()
def testapp():
    tapp = my_app
    tapp.config.update({
        "TESTING": True,
        "TABLENAME": "test_ddb_tablename",
        "SQLITE3DB": "../db/test-sql3-database.sdb",
    })

    # other setup can go here

    yield tapp

    # clean up / reset resources here


@pytest.fixture()
def client(testapp):
    return testapp.test_client()
