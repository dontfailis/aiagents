import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000';

const StorySession = () => {
  const { sessionId } = useParams();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingChoice, setProcessingChoice] = useState(false);

  const fetchSession = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/sessions/${sessionId}`);
      setSession(response.data);
    } catch (err) {
      setError('Failed to load story session.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSession();
  }, [sessionId]);

  const handleChoice = async (choiceId: number) => {
    setProcessingChoice(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/sessions/${sessionId}/choices`, {
        choice_id: choiceId
      });
      setSession(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process choice.');
    } finally {
      setProcessingChoice(false);
    }
  };

  const handleConclude = async () => {
    setProcessingChoice(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/sessions/${sessionId}/conclude`);
      setSession(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to conclude session.');
    } finally {
      setProcessingChoice(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Entering the story...</div>;
  if (!session) return <div className="p-8 text-center">Session not found.</div>;

  const { current_scene, status, summary, history } = session;

  if (status === 'completed') {
    return (
      <div className="max-w-3xl mx-auto p-8 bg-white rounded shadow">
        <h2 className="text-3xl font-bold mb-6 text-center">Adventure Concluded</h2>
        <div className="bg-amber-50 p-6 rounded mb-8 border-l-4 border-amber-500">
          <h3 className="font-bold text-xl mb-2">The Chronicle of Your Journey</h3>
          <p className="text-lg leading-relaxed">{summary}</p>
        </div>
        <div className="text-center">
          <Link to="/" className="bg-blue-600 text-white font-bold py-3 px-8 rounded">Return Home</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-8 bg-white rounded shadow">
      {error && <div className="bg-red-100 text-red-700 p-4 mb-4 rounded">{error}</div>}
      
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <span className="text-sm font-bold text-gray-500 uppercase tracking-widest">Scene {current_scene.scene_number}</span>
          <span className="text-xs text-gray-400 italic">{history.length} events recorded</span>
        </div>
        <div className="text-xl leading-relaxed text-gray-800 space-y-4 whitespace-pre-wrap">
          {current_scene.narrative}
        </div>
      </div>

      <div className="grid gap-4 mt-8">
        {current_scene.choices.map((choice: any) => (
          <button
            key={choice.id}
            onClick={() => handleChoice(choice.id)}
            disabled={processingChoice}
            className={`text-left p-4 border-2 border-blue-100 hover:border-blue-500 hover:bg-blue-50 rounded-xl transition-all font-medium text-lg ${processingChoice ? 'opacity-50 grayscale' : ''}`}
          >
            {choice.text}
          </button>
        ))}
      </div>

      {current_scene.scene_number >= 5 && (
        <div className="mt-12 pt-8 border-t text-center">
          <p className="text-gray-500 mb-4 italic text-sm">You feel the narrative reaching a natural conclusion...</p>
          <button 
            onClick={handleConclude} disabled={processingChoice}
            className="bg-amber-600 text-white font-bold py-2 px-6 rounded hover:bg-amber-700"
          >
            {processingChoice ? 'Concluding...' : 'Bring Adventure to a Close'}
          </button>
        </div>
      )}
    </div>
  );
};

export default StorySession;
