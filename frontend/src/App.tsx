import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import CreateCharacterForm from './components/CreateCharacterForm';
import CreateWorldForm from './components/CreateWorldForm';
import JoinWorldScreen from './components/JoinWorldScreen';
import LandingPage from './components/LandingPage';
import StorySession from './components/StorySession';
import WorldChronicle from './components/WorldChronicle';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/join" element={<JoinWorldScreen />} />
        <Route path="/create-world" element={<CreateWorldForm />} />
        <Route path="/create-character/:worldId" element={<CreateCharacterForm />} />
        <Route path="/session/:sessionId" element={<StorySession />} />
        <Route path="/chronicle/:worldId" element={<WorldChronicle />} />
      </Routes>
    </Router>
  );
}

export default App;
