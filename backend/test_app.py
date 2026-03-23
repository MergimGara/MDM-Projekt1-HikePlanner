import pytest
from backend.app import app as flask_app

@pytest.fixture
def app():
    # The flask_app is configured at import time, which is fine for these tests
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_predict_api(client):
    """Test the /api/predict endpoint with valid parameters."""
    # Test with a sample hike
    response = client.get('/api/predict?uphill=300&downhill=300&length=10000')
    assert response.status_code == 200
    
    json_data = response.get_json()
    # Ensure all prediction keys are present
    assert 'time' in json_data
    assert 'linear' in json_data
    assert 'din33466' in json_data
    assert 'sac' in json_data
    
    # Check if the time format is plausible (e.g., HH:MM:SS)
    assert len(json_data['time']) > 5
    assert ":" in json_data['time']

def test_predict_api_defaults(client):
    """Test the /api/predict endpoint with default (zero) parameters."""
    response = client.get('/api/predict')
    assert response.status_code == 200
    json_data = response.get_json()
    # With no input, times should be '0:00:00' or similar
    assert json_data['din33466'] == '0:00:00'

def test_index_route(client):
    """Test the index route, which should serve the frontend."""
    response = client.get('/')
    assert response.status_code == 200
    # A simple check to see if it's returning HTML from the Svelte build
    assert b'<!DOCTYPE html>' in response.data
    # A more specific check for your app's content might be useful
    assert b'SvelteKit' in response.data
