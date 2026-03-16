import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';

const Home = () => (
  <div className="p-8 text-center">
    <h1 className="text-4xl font-bold mb-4">Shared AI Storytelling RPG</h1>
    <p className="mb-6">Create or join an evolving, persistent world with your friends.</p>
    <div className="flex justify-center gap-4">
      <a href="/create-world" className="bg-blue-600 text-white px-6 py-2 rounded">Create World</a>
      <button className="bg-gray-200 px-6 py-2 rounded">Join with Code</button>
    </div>
  </div>
);

const CreateWorld = () => (
  <div className="p-8">
    <h2 className="text-2xl font-bold mb-4">Define Your World</h2>
    <p>Placeholder for World Creation Form...</p>
    <a href="/" className="text-blue-500 underline">Back home</a>
  </div>
);

const CreateCharacter = () => (
  <div className="p-8">
    <h2 className="text-2xl font-bold mb-4">Create Your Character</h2>
    <p>Placeholder for Character Creation Form...</p>
    <a href="/" className="text-blue-500 underline">Back home</a>
  </div>
);

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-white text-gray-900 font-sans">
        <nav className="p-4 border-b">
          <a href="/" className="font-bold">RPG Conductor</a>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/create-world" element={<CreateWorld />} />
          <Route path="/create-character/:worldId" element={<CreateCharacter />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
