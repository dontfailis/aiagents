import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestSessions(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Create a world and character first
        world_resp = self.client.post('/api/worlds', json={
            'name': 'Test World', 'era': 'Medieval Fantasy', 'environment': 'Woods', 'tone': 'Adventure'
        })
        self.world_id = world_resp.json()['id']
        
        char_resp = self.client.post('/api/characters', json={
            'world_id': self.world_id, 'name': 'Test Hero', 'age': 20, 
            'archetype': 'Warrior', 'backstory': 'A hero.', 'visual_description': 'Armor.'
        })
        self.char_id = char_resp.json()['id']

    def test_create_session(self):
        response = self.client.post('/api/sessions', json={
            'character_id': self.char_id,
            'world_id': self.world_id
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['character_id'], self.char_id)
        self.assertIn('current_scene', data)
        self.assertIn('choices', data['current_scene'])

    def test_get_session(self):
        create_resp = self.client.post('/api/sessions', json={
            'character_id': self.char_id,
            'world_id': self.world_id
        })
        session_id = create_resp.json()['id']
        
        response = self.client.get(f'/api/sessions/{session_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], session_id)

    def test_submit_choice(self):
        create_resp = self.client.post('/api/sessions', json={
            'character_id': self.char_id,
            'world_id': self.world_id
        })
        session_id = create_resp.json()['id']
        choice_id = create_resp.json()['current_scene']['choices'][0]['id']
        
        response = self.client.post(f'/api/sessions/{session_id}/choices', json={
            'choice_id': choice_id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('current_scene', data)
        self.assertEqual(data['current_scene']['scene_number'], 2)
        self.assertTrue(len(data['history']) > 0)

if __name__ == '__main__':
    unittest.main()
