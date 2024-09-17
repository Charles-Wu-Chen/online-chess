import React from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import ChessGame from './Chessboard';

const App: React.FC = () => {
  return (
    <DndProvider backend={HTML5Backend}>
      <div className="App">
        <h1>Chess Game</h1>
        <ChessGame />
      </div>
    </DndProvider>
  );
};

export default App;