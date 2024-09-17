import React, { useState, useRef, useEffect } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';

const ChessGame: React.FC = () => {
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

  function makeAMove(move: any) {
    const gameCopy = new Chess(game.fen());
    try {
      const result = gameCopy.move(move);
      setGame(gameCopy);
      
      // Check for checkmate
      if (gameCopy.isGameOver()) {
        setMessage(gameCopy.isCheckmate() ? 'Checkmate!' : 'Game Over!');
      } else {
        setMessage(''); // Clear message if it's a valid move
      }
      
      return result;
    } catch (error) {
      setMessage('Invalid move');
      return null;
    }
  }

  function onDrop(sourceSquare: string, targetSquare: string) {
    const move = makeAMove({
      from: sourceSquare,
      to: targetSquare,
      promotion: 'q', // always promote to a queen for example simplicity
    });

    // illegal move
    if (move === null) return false;
    return true;
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
    }}>
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
    </div>
  );
};

export default ChessGame;