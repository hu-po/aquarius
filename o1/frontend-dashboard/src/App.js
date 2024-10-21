import React from 'react';
import FishPlot from './components/FishPlot';
import RecentImage from './components/RecentImage';
import LLMReply from './components/LLMReply';
import Stats from './components/Stats';

const App = () => {
    return (
        <div>
            <h1>Aquarium Monitor Dashboard</h1>
            <FishPlot />
            <RecentImage />
            <LLMReply />
            <Stats />
        </div>
    );
};

export default App;
