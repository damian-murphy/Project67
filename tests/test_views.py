""" Test each view is working """
def test_home(client):
    """ With the app, get home page, check for title """
    response = client.get('/')
    assert b'<title>The Projects File - Projects: Currently Active' in response.data

def test_list(client):
    """ Check that the list all page works """
    response = client.get('/list')
    assert b'Projects: All' in response.data
    assert b'number' in response.data
    assert b'idea' in response.data
    assert b'created' in response.data
    assert b'done' in response.data

def test_paused(client):
    response = client.get('/paused')
    assert b'Projects: Paused' in response.data

def test_done(client):
    response = client.get('/done')
    assert b'Projects: Completed' in response.data

def test_habits(client):
    response = client.get('/habits')
    assert b'Projects: Habits' in response.data

def test_show_project(client):
    response = client.get('/project/1')
    assert b'Project No.1' in response.data
    assert b'Created: Fri, 01 Nov, 1996, 12:00 AM' in response.data
