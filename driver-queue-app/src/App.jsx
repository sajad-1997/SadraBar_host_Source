import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import DriverInfo from './pages/DriverInfo';
import DriverRegistration from './pages/DriverRegistration';
import QueuePage from './pages/QueuePage';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/driver-info" element={<DriverInfo />} />
        <Route path="/driver-registration" element={<DriverRegistration />} />
        <Route path="/queue" element={<QueuePage />} />
      </Routes>
    </Router>
  );
}

export default App;
