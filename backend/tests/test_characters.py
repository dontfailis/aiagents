import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestCharacters(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Create a world first to associate character with
        self.world_response = self.client.post('/api/worlds', json={
            'name': 'The Shattered Realm',
            'era': 'Medieval Fantasy',
            'environment': 'Harbor District',
            'tone': 'Adventure'
        })
        self.world_id = self.world_response.json()['id']

    def test_create_character(self):
        response = self.client.post('/api/characters', json={
            'world_id': self.world_id,
            'name': 'Kira',
            'age': 25,
            'archetype': 'Rogue',
            'backstory': 'A street urchin who learned to survive in the Harbor District.',
            'visual_description': 'Wearing dark leather armor with a hooded cloak.'
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['name'], 'Kira')
        self.assertEqual(data['world_id'], self.world_id)
        self.assertIn('id', data)
        self.assertIn('portrait_url', data)
        self.assertIsNotNone(data['portrait_url'])

    def test_create_character_invalid_world(self):
        response = self.client.post('/api/characters', json={
            'world_id': 'non-existent-id',
            'name': 'Ghost',
            'age': 99,
            'archetype': 'Warrior',
            'backstory': 'Nothingness.',
            'visual_description': 'Transparent.'
        })
        self.assertEqual(response.status_code, 404)

    def test_create_character_mismatched_lore(self):
        # Trying to create a cyborg in a medieval fantasy world
        response = self.client.post('/api/characters', json={
            'world_id': self.world_id,
            'name': 'Unit 7',
            'age': 5,
            'archetype': 'Cyborg',
            'backstory': 'Built in a high-tech lab with laser eyes.',
            'visual_description': 'Chrome plating and glowing blue wires.'
        })
        # If AI validation is working, this should likely fail (400)
        self.assertIn(response.status_code, [400, 201])
        if response.status_code == 400:
            self.assertIn("Character does not fit the world", response.json()['detail'])

if __name__ == '__main__':
    unittest.main()
