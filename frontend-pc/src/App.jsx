import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components';
import { StreamsPage } from './pages/StreamsPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { InfoPage } from './pages/InfoPage';
import './styles/components.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<StreamsPage />} />
          <Route path="analysis" element={<AnalysisPage />} />
          <Route path="info" element={<InfoPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;