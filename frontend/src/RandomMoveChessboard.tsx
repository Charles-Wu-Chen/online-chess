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

  function makeRandomMove(currentGame: Chess) {
    const possibleMoves = currentGame.moves();

    // Exit if the game is over
    if (currentGame.isGameOver() || currentGame.isDraw() || possibleMoves.length === 0) {
      setMessage(currentGame.isCheckmate() ? 'Checkmate!' : 'Game Over!');
      return;
    }

    const randomIndex = Math.floor(Math.random() * possibleMoves.length);
    const randomMove = possibleMoves[randomIndex];
    
    const gameCopy = new Chess(currentGame.fen());
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
    try {
      const gameCopy = new Chess(game.fen());
      const move = gameCopy.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q', // always promote to queen for simplicity
      });

      // If move is null, it's an invalid move
      if (move === null) {
        setMessage('Invalid move');
        return false;
      }

      setGame(gameCopy);

      // Check for game end conditions after player's move
      if (gameCopy.isCheckmate()) {
        setMessage('Checkmate!');
      } else if (gameCopy.isDraw()) {
        setMessage('Draw!');
      } else {
        // Make a random move for the computer using the updated game state
        setTimeout(() => makeRandomMove(gameCopy), 300);
      }

      return true;
    } catch (error) {
      console.error('Error in onDrop:', error);
      setMessage('Invalid move');
      return false;
    }
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