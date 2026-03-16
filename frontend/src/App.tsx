import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import CreateWorldForm from './components/CreateWorldForm';
import CreateCharacterForm from './components/CreateCharacterForm';
import StorySession from './components/StorySession';

const Home = () => (
  <div className="p-8 text-center max-w-4xl mx-auto">
    <h1 className="text-4xl font-bold mb-4">Shared AI Storytelling RPG</h1>
    <p className="text-xl mb-6">Create or join an evolving, persistent world with your friends.</p>
    <div className="flex justify-center gap-4">
      <Link to="/create-world" className="bg-blue-600 text-white px-6 py-2 rounded font-bold">Create World</Link>
      <button className="bg-gray-200 px-6 py-2 rounded font-bold">Join with Code</button>
    </div>
  </div>
);

const CreateWorld = () => (
  <div className="p-8 bg-gray-50 min-h-screen">
    <Link to="/" className="text-blue-500 underline mb-4 inline-block">&larr; Back home</Link>
    <CreateWorldForm />
  </div>
);

const CreateCharacter = () => (
  <div className="p-8 bg-gray-50 min-h-screen">
    <Link to="/" className="text-blue-500 underline mb-4 inline-block">&larr; Back home</Link>
    <CreateCharacterForm />
  </div>
);

const SessionPage = () => (
  <div className="p-8 bg-gray-100 min-h-screen">
    <StorySession />
  </div>
);

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-white text-gray-900 font-sans">
        <nav className="p-4 border-b">
          <Link to="/" className="font-bold">RPG Conductor</Link>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/create-world" element={<CreateWorld />} />
          <Route path="/create-character/:worldId" element={<CreateCharacter />} />
          <Route path="/session/:sessionId" element={<SessionPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
