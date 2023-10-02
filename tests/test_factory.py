from projects import app


def test_hello(client):
    """ With the app, get the hello page, confirming app at least runs and does a basic
    """
    response = client.get('/hello')
    assert response.data == b'<h1>Hello!</h1>'

def test_home(client):
    """ With the app, get home page, check for title """
    response = client.get('/')
    assert response.data == b'<title>The Projects File - Projects: Currently Active'
