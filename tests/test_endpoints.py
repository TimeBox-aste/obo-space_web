import requests
import pytest

@pytest.fixture
def session():
    """Create a requests session for testing"""
    with requests.Session() as session:
        yield session
    
@pytest.fixture
def base_url():
    """Base URL for the API"""
    return 'http://localhost:5000'

def test_register(session, base_url):
    """Test the registration endpoint"""
    response = session.post(f'{base_url}/api/v1/register', json={
        'full_name': 'John Doe',
        'email': 'john@example.com',
        'accept_license': True,
        'accept_age': True
    })
    response.raise_for_status()
    data = response.json()
    assert response.status_code == 200
    assert data['success'] is True

def test_register_missing_fields(session, base_url):
    """Test registration with missing fields"""
    response = session.post(f'{base_url}/api/v1/register', json={
        'full_name': '',
        'email': 'john@example.com',
        'accept_license': True,
        'accept_age': True
    })
    data = response.json()
    assert response.status_code == 400
    assert data['success'] is False
    assert data['message'] == 'All fields are required'

def test_index(session, base_url):
    """Test the index endpoint"""
    response = session.get(f'{base_url}/')
    response.raise_for_status()
    data = response.text
    assert response.status_code == 200
    assert 'Obo-Space' in data
