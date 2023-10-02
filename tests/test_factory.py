
def test_hello(client):
    """ With the app, get the hello page, confirming app at least runs and does a basic
    """
    response = client.get('/hello')
    assert response.data == b'<h1>Hello!</h1>'
