import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components';
import { StreamsPage } from './pages/StreamsPage';
import { AnalysisPage } from './pages/AnalysisPage';
import './styles/components.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<StreamsPage />} />
          <Route path="analysis" element={<AnalysisPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;