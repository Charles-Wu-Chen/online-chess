import React, { useState, useRef, useEffect } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';

const RandomMoveChessboard: React.FC = () => {
  const [game, setGame] = useState<Chess>(new Chess());
  const [boardWidth, setBoardWidth] = useState(400);
  const [message, setMessage] = useState('');
  const boardContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateDimensions = () => {
      if (boardContainerRef.current) {
        setBoardWidth(boardContainerRef.current.offsetWidth);
      }
    };

    window.addEventListener('resize', updateDimensions);
    updateDimensions();

    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  function makeRandomMove() {
    const possibleMoves = game.moves();

    // Exit if the game is over
    if (game.isGameOver() || game.isDraw() || possibleMoves.length === 0) {
      setMessage(game.isCheckmate() ? 'Checkmate!' : 'Game Over!');
      return;
    }

    const randomIndex = Math.floor(Math.random() * possibleMoves.length);
    const randomMove = possibleMoves[randomIndex];
    
    const gameCopy = new Chess(game.fen());
    gameCopy.move(randomMove);
    setGame(gameCopy);

    // Check for checkmate after computer's move
    if (gameCopy.isCheckmate()) {
      setMessage('Checkmate!');
    } else if (gameCopy.isDraw()) {
      setMessage('Draw!');
    } else {
      setMessage('');
    }
  }

  function onDrop(sourceSquare: string, targetSquare: string) {
    const gameCopy = new Chess(game.fen());
    const move = gameCopy.move({
      from: sourceSquare,
      to: targetSquare,
      promotion: 'q', // always promote to queen for simplicity
    });

    // Illegal move
    if (move === null) {
      setMessage('Invalid move');
      return false;
    }

    setGame(gameCopy);

    // Check for checkmate after player's move
    if (gameCopy.isCheckmate()) {
      setMessage('Checkmate!');
    } else if (gameCopy.isDraw()) {
      setMessage('Draw!');
    } else {
      // Make a random move for the computer
      setTimeout(makeRandomMove, 300);
    }

    return true;
  }

  function resetGame() {
    setGame(new Chess());
    setMessage('');
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '2rem',
    }}>
      <h2>Random Move Chessboard</h2>
      <div ref={boardContainerRef} style={{ width: '400px', maxWidth: '100%' }}>
        <Chessboard 
          position={game.fen()} 
          onPieceDrop={onDrop} 
          boardWidth={boardWidth}
        />
      </div>
      {message && (
        <div style={{ marginTop: '20px', fontSize: '18px', fontWeight: 'bold' }}>
          {message}
        </div>
      )}
      <button 
        onClick={resetGame}
        style={{
          marginTop: '20px',
          padding: '10px 20px',
          fontSize: '16px',
          cursor: 'pointer',
        }}
      >
        Reset Game
      </button>
    </div>
  );
};

export default RandomMoveChessboard;