import React, { useState, useRef, useEffect } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import axios from 'axios';

const RandomMoveChessboard: React.FC = () => {
  const [game, setGame] = useState<Chess>(new Chess());
  const [boardWidth, setBoardWidth] = useState(400);
  const [message, setMessage] = useState('');
  const [evaluation, setEvaluation] = useState<number | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [sharpness, setSharpness] = useState<number | null>(null);
  const [isCalculatingSharpness, setIsCalculatingSharpness] = useState(false);
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

  const evaluatePosition = async () => {
    setIsEvaluating(true);
    setEvaluation(null);
    try {
      const response = await axios.post('http://localhost:5000/evaluate', {
        fen: game.fen(),
        depth: 10
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      if (response.status === 202) {
        // Start polling for results
        pollForEvaluation();
      } else {
        console.error('Unexpected response:', response);
        setIsEvaluating(false);
      }
    } catch (error) {
      console.error('Error evaluating position:', error);
      if (axios.isAxiosError(error)) {
        console.error('Axios error details:', error.response?.data);
      }
      setIsEvaluating(false);
    }
  };

  const pollForEvaluation = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get('http://localhost:5000/evaluation-result');
        if (response.data.status === 'completed') {
          setEvaluation(response.data.evaluation);
          setIsEvaluating(false);
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Error polling for evaluation:', error);
        setIsEvaluating(false);
        clearInterval(pollInterval);
      }
    }, 1000); // Poll every second

    // Stop polling after 30 seconds if no result
    setTimeout(() => {
      clearInterval(pollInterval);
      setIsEvaluating(false);
    }, 30000);
  };

  const calculateSharpness = async () => {
    setIsCalculatingSharpness(true);
    setSharpness(null);
    try {
      const response = await axios.post('http://localhost:5000/sharpness', {
        fen: game.fen()
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      if (response.status === 202) {
        // Start polling for results
        pollForSharpness();
      } else {
        console.error('Unexpected response:', response);
        setIsCalculatingSharpness(false);
      }
    } catch (error) {
      console.error('Error calculating sharpness:', error);
      if (axios.isAxiosError(error)) {
        console.error('Axios error details:', error.response?.data);
      }
      setIsCalculatingSharpness(false);
    }
  };

  const pollForSharpness = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get('http://localhost:5000/sharpness-result');
        if (response.data.status === 'completed') {
          setSharpness(response.data.sharpness);
          setIsCalculatingSharpness(false);
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Error polling for sharpness:', error);
        setIsCalculatingSharpness(false);
        clearInterval(pollInterval);
      }
    }, 1000); // Poll every second

    // Stop polling after 30 seconds if no result
    setTimeout(() => {
      clearInterval(pollInterval);
      setIsCalculatingSharpness(false);
    }, 30000);
  };

  useEffect(() => {
    evaluatePosition();
    calculateSharpness();
  }, [game]);

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
      flexDirection: 'row',
      alignItems: 'flex-start',
      padding: '2rem',
    }}>
      <div>
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
      <div style={{ marginLeft: '2rem', minWidth: '200px' }}>
        <h3>Evaluation</h3>
        {isEvaluating ? (
          <p>Evaluating...</p>
        ) : evaluation !== null ? (
          <p>Current position: {evaluation / 100} pawns</p>
        ) : (
          <p>No evaluation available</p>
        )}
        <h3>Sharpness</h3>
        {isCalculatingSharpness ? (
          <p>Calculating sharpness...</p>
        ) : sharpness !== null ? (
          <p>Position sharpness: {sharpness.toFixed(4)}</p>
        ) : (
          <p>No sharpness data available</p>
        )}
        <h3>Current Position (FEN)</h3>
        <p style={{ wordBreak: 'break-all' }}>{game.fen()}</p>
      </div>
    </div>
  );
};

export default RandomMoveChessboard;