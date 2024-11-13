import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components';
import { HomePage, StreamsPage, AnalysisPage, InfoPage, RobotPage } from './pages';
import './styles/components.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/streams" element={<StreamsPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/info" element={<InfoPage />} />
          <Route path="/robot" element={<RobotPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;