import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestWorlds(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_world(self):
        response = self.client.post('/api/worlds', json={
            'name': 'The Shattered Realm',
            'era': 'Medieval Fantasy',
            'environment': 'Harbor District',
            'tone': 'Adventure',
            'description': 'A world where magic is fading and chaos is rising.'
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['name'], 'The Shattered Realm')
        self.assertIn('id', data)
        self.assertIn('share_code', data)
        return data['id']

    def test_get_world(self):
        # First create a world
        create_response = self.client.post('/api/worlds', json={
            'name': 'Test World',
            'era': 'Post-Apocalyptic',
            'environment': 'Wilderness',
            'tone': 'Survival',
            'description': 'Test description'
        })
        world_id = create_response.json()['id']
        
        # Then retrieve it
        response = self.client.get(f'/api/worlds/{world_id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Test World')
        self.assertEqual(data['id'], world_id)

if __name__ == '__main__':
    unittest.main()
