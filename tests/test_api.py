import pytest

def test_health(client):
    r=client.get('/api/health')
    assert r.status_code==200, f'health endpoint returned {r.status_code}'

def test_create_resource(client):
    r=client.post('/api/events', json={'name':'patient-admission-001','description':'QA test patient event','status':'pending','event_type':'admission'})
    assert r.status_code in (200,201), f'create returned {r.status_code}: {r.text}'
    data=r.json()
    assert 'id' in data or 'name' in data

def test_list_resources(client):
    r=client.get('/api/events')
    assert r.status_code==200, f'list returned {r.status_code}'
    assert isinstance(r.json(),(list,dict))

def test_invalid_input(client):
    r=client.post('/api/events', json={})
    assert 400<=r.status_code<500, f'empty body should return 4xx, got {r.status_code}'

def test_analytics(client):
    r=client.get('/api/analytics')
    assert r.status_code==200, f'analytics returned {r.status_code}'
