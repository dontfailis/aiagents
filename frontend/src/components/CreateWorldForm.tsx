import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000';

const CreateWorldForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    era: 'Medieval Fantasy',
    environment: 'Harbor District',
    tone: 'Adventure',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/worlds`, formData);
      const worldId = response.data.id;
      navigate(`/create-character/${worldId}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create world. Make sure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-6">Define Your Storytelling World</h2>
      {error && <div className="bg-red-100 text-red-700 p-4 mb-4 rounded">{error}</div>}
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="block font-bold mb-1">World Name</label>
          <input 
            type="text" name="name" value={formData.name} onChange={handleChange} required 
            className="w-full border p-2 rounded" placeholder="e.g. The Shattered Realm"
          />
        </div>
        <div>
          <label className="block font-bold mb-1">Era</label>
          <select name="era" value={formData.era} onChange={handleChange} className="w-full border p-2 rounded">
            <option>Medieval Fantasy</option>
            <option>Post-Apocalyptic</option>
            <option>Modern Mystery</option>
            <option>Space Opera</option>
          </select>
        </div>
        <div>
          <label className="block font-bold mb-1">Environment</label>
          <input 
            type="text" name="environment" value={formData.environment} onChange={handleChange} required 
            className="w-full border p-2 rounded" placeholder="e.g. Harbor District, Desert Pass, Floating Islands"
          />
        </div>
        <div>
          <label className="block font-bold mb-1">Tone</label>
          <select name="tone" value={formData.tone} onChange={handleChange} className="w-full border p-2 rounded">
            <option>Adventure</option>
            <option>Grimdark</option>
            <option>Whimsical</option>
            <option>Survival</option>
          </select>
        </div>
        <div>
          <label className="block font-bold mb-1">Initial Description (Optional)</label>
          <textarea 
            name="description" value={formData.description} onChange={handleChange}
            className="w-full border p-2 rounded h-24" placeholder="Briefly describe the state of the world..."
          ></textarea>
        </div>
        <button 
          type="submit" disabled={loading}
          className={`bg-blue-600 text-white font-bold py-2 px-4 rounded ${loading ? 'opacity-50' : ''}`}
        >
          {loading ? 'Creating World...' : 'Create World'}
        </button>
      </form>
    </div>
  );
};

export default CreateWorldForm;
