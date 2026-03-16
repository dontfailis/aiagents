import unittest
import asyncio
from app.ai import generate_world_intro, generate_next_scene

class TestAI(unittest.TestCase):
    def test_generate_world_intro(self):
        world_data = {
            'name': 'The Shattered Realm',
            'era': 'Medieval Fantasy',
            'environment': 'Harbor District',
            'tone': 'Adventure',
            'description': 'A world where magic is fading.'
        }
        
        intro = asyncio.run(generate_world_intro(world_data))
        
        self.assertIsInstance(intro, str)
        self.assertTrue(len(intro) > 10)
        self.assertIn('Shattered Realm', intro)

    def test_generate_next_scene(self):
        world_data = {'name': 'Test World', 'era': 'Medieval', 'tone': 'Adventure'}
        char_data = {'name': 'Hero', 'age': 20, 'archetype': 'Warrior', 'backstory': 'A brave hero.'}
        
        scene = asyncio.run(generate_next_scene(world_data, char_data))
        
        self.assertIn('narrative', scene)
        self.assertIn('choices', scene)
        self.assertTrue(len(scene['choices']) >= 2)
        self.assertIsInstance(scene['choices'][0]['text'], str)

if __name__ == '__main__':
    unittest.main()
