import sys
import unittest.mock as mock
import pytest
import pandas as pd
import io

# --- PROFESSIONAL MOCKING (NIVEAU 6.0) ---
# Wir simulieren ein trainiertes Modell
class MockModel:
    def predict(self, df):
        return [3600.0]

# Wir erstellen einen Mock für die open-Funktion, der nur bei den Pickles eingreift
original_open = open

def smart_open(file, mode='r', *args, **kwargs):
    if str(file).endswith('.pkl'):
        return io.BytesIO(b"dummy_data")
    return original_open(file, mode, *args, **kwargs)

mock_blob_service = mock.MagicMock()
mock_container_client = mock.MagicMock()
mock_blob_service.get_container_client.return_value = mock_container_client
mock_container_client.list_blobs.return_value = []

with mock.patch('azure.storage.blob.BlobServiceClient.from_connection_string', return_value=mock_blob_service), \
     mock.patch('pickle.load', return_value=MockModel()), \
     mock.patch('builtins.open', side_effect=smart_open), \
     mock.patch('pathlib.Path.exists', return_value=True), \
     mock.patch('shutil.rmtree'):
    
    from backend.app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_predict_api_success(client):
    response = client.get('/api/predict?uphill=500&downhill=200&length=10000')
    assert response.status_code == 200
    data = response.get_json()
    assert 'time' in data
    assert 'sac' in data

def test_predict_api_edge_cases(client):
    response = client.get('/api/predict?uphill=-100&downhill=-50&length=-1000')
    assert response.status_code == 200
    
def test_predict_api_missing_params(client):
    response = client.get('/api/predict')
    assert response.status_code == 200
    data = response.get_json()
    assert data['din33466'] == '0:00:00'

def test_index_route(client):
    response = client.get('/')
    assert response.status_code in [200, 404]
