import unittest
import asyncio
from app.ai import generate_world_intro

class TestAI(unittest.TestCase):
    def test_generate_world_intro(self):
        world_data = {
            'name': 'The Shattered Realm',
            'era': 'Medieval Fantasy',
            'environment': 'Harbor District',
            'tone': 'Adventure',
            'description': 'A world where magic is fading.'
        }
        
        # Use asyncio.run to execute the async function
        intro = asyncio.run(generate_world_intro(world_data))
        
        self.assertIsInstance(intro, str)
        self.assertTrue(len(intro) > 10)
        self.assertIn('Shattered Realm', intro)

if __name__ == '__main__':
    unittest.main()
