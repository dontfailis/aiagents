import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000';

const CreateCharacterForm = () => {
  const { worldId } = useParams();
  const [world, setWorld] = useState<any>(null);
  const [formData, setFormData] = useState({
    world_id: worldId,
    name: '',
    age: 25,
    archetype: 'Rogue',
    backstory: '',
    visual_description: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [character, setCharacter] = useState<any>(null);

  useEffect(() => {
    const fetchWorld = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/worlds/${worldId}`);
        setWorld(response.data);
      } catch (err) {
        setError('Failed to load world context.');
      }
    };
    fetchWorld();
  }, [worldId]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/characters`, formData);
      setCharacter(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create character.');
    } finally {
      setLoading(false);
    }
  };

  if (!world && !error) return <div>Loading world context...</div>;

  const handleStartAdventure = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/sessions`, {
        character_id: character.id,
        world_id: worldId
      });
      navigate(`/session/${response.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start adventure.');
    } finally {
      setLoading(false);
    }
  };

  if (character) {
    return (
      <div className="max-w-2xl mx-auto p-8 bg-white rounded shadow text-center">
        <h2 className="text-3xl font-bold mb-4">Character Created!</h2>
        <div className="mb-6">
          <img src={character.portrait_url} alt={character.name} className="w-64 h-64 mx-auto rounded-full border-4 border-blue-500 object-cover" />
        </div>
        <h3 className="text-2xl font-bold">{character.name}</h3>
        <p className="text-gray-600 mb-4">{character.archetype}, Age {character.age}</p>
        <div className="bg-blue-50 p-4 rounded mb-6 text-left">
          <h4 className="font-bold mb-1">AI World-Fit Analysis:</h4>
          <p className="italic text-sm">{character.fit_reasoning}</p>
        </div>
        <div className="flex justify-center gap-4">
          <button 
            onClick={handleStartAdventure} disabled={loading}
            className="bg-green-600 text-white font-bold py-2 px-6 rounded"
          >
            {loading ? 'Starting...' : 'Start First Adventure'}
          </button>
          <Link to="/" className="bg-gray-200 py-2 px-6 rounded">Back Home</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-8 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-2">Create Your Character</h2>
      <p className="text-gray-600 mb-6 italic">World: {world?.name || '...'}</p>
      
      {error && <div className="bg-red-100 text-red-700 p-4 mb-4 rounded">{error}</div>}
      
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block font-bold mb-1">Name</label>
            <input 
              type="text" name="name" value={formData.name} onChange={handleChange} required 
              className="w-full border p-2 rounded" placeholder="Character Name"
            />
          </div>
          <div>
            <label className="block font-bold mb-1">Age</label>
            <input 
              type="number" name="age" value={formData.age} onChange={handleChange} required 
              className="w-full border p-2 rounded"
            />
          </div>
        </div>
        <div>
          <label className="block font-bold mb-1">Archetype</label>
          <select name="archetype" value={formData.archetype} onChange={handleChange} className="w-full border p-2 rounded">
            <option>Rogue</option>
            <option>Warrior</option>
            <option>Scholar</option>
            <option>Survivor</option>
            <option>Merchant</option>
            <option>Wanderer</option>
          </select>
        </div>
        <div>
          <label className="block font-bold mb-1">Backstory</label>
          <textarea 
            name="backstory" value={formData.backstory} onChange={handleChange} required
            className="w-full border p-2 rounded h-24" placeholder="Where do they come from? What are their motivations?"
          ></textarea>
        </div>
        <div>
          <label className="block font-bold mb-1">Visual Description</label>
          <textarea 
            name="visual_description" value={formData.visual_description} onChange={handleChange} required
            className="w-full border p-2 rounded h-24" placeholder="Describe their appearance for the AI portrait..."
          ></textarea>
        </div>
        <button 
          type="submit" disabled={loading}
          className={`bg-blue-600 text-white font-bold py-2 px-4 rounded ${loading ? 'opacity-50' : ''}`}
        >
          {loading ? 'Creating Character & Portrait...' : 'Create Character'}
        </button>
      </form>
    </div>
  );
};

export default CreateCharacterForm;
