import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Chessboard from './Chessboard';
import RandomMoveChessboard from './RandomMoveChessboard';
import Navigation from './Navigation';

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <Routes>
          <Route path="/" element={<Chessboard />} />
          <Route path="/default" element={<Chessboard />} />
          <Route path="/random-move" element={<RandomMoveChessboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;