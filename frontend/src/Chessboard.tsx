import React, { useState, useRef, useEffect } from 'react';
import { Chess } from 'chess.js';
import { Chessboard as ReactChessboard } from 'react-chessboard';
import axios from 'axios';

interface BestLine {
  moves: string;
  score: number;
  sharpness: number;
}

const ChessGame: React.FC = () => {
  const [game, setGame] = useState<Chess>(new Chess());
  const [boardWidth, setBoardWidth] = useState(400);
  const [message, setMessage] = useState('');
  const [evaluation, setEvaluation] = useState<number | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [sharpness, setSharpness] = useState<number | null>(null);
  const [isCalculatingSharpness, setIsCalculatingSharpness] = useState(false);
  const [bestLines, setBestLines] = useState<BestLine[]>([]);
  const [isLoadingBestLines, setIsLoadingBestLines] = useState(false);
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

  const getBestLines = async () => {
    setIsLoadingBestLines(true);
    setBestLines([]);
    try {
      const response = await axios.post('http://localhost:5000/best-lines', {
        current_fen: game.fen(),
        number_of_lines: 3,
        depth: 20
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      if (response.status === 202) {
        // Start polling for results
        pollForBestLines();
      } else {
        console.error('Unexpected response:', response);
        setIsLoadingBestLines(false);
      }
    } catch (error) {
      console.error('Error getting best lines:', error);
      if (axios.isAxiosError(error)) {
        console.error('Axios error details:', error.response?.data);
      }
      setIsLoadingBestLines(false);
    }
  };

  const pollForBestLines = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get('http://localhost:5000/best-lines-result');
        if (response.data.status === 'completed') {
          setBestLines(response.data.best_lines);
          setIsLoadingBestLines(false);
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Error polling for best lines:', error);
        setIsLoadingBestLines(false);
        clearInterval(pollInterval);
      }
    }, 1000); // Poll every second

    // Stop polling after 30 seconds if no result
    setTimeout(() => {
      clearInterval(pollInterval);
      setIsLoadingBestLines(false);
    }, 30000);
  };

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

      // Evaluate position, calculate sharpness, and get best lines after each move
      evaluatePosition();
      calculateSharpness();
      getBestLines();
      
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
      flexDirection: 'row',
      alignItems: 'flex-start',
      padding: '2rem',
    }}>
      <div>
        <h2>Default Chessboard</h2>
        <div ref={boardContainerRef} style={{ width: '400px', maxWidth: '100%' }}>
          <ReactChessboard 
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
        <h3>Best Lines</h3>
        {isLoadingBestLines ? (
          <p>Loading best lines...</p>
        ) : bestLines.length > 0 ? (
          <ul>
            {bestLines.map((line, index) => (
              <li key={index}>
                <strong>Line {index + 1}:</strong><br />
                Sharpness: {line.sharpness.toFixed(4)}
                Score: {line.score / 100} pawns<br />
                Moves: {line.moves}<br />
              </li>
            ))}
          </ul>
        ) : (
          <p>No best lines available</p>
        )}
        <h3>Current Position (FEN)</h3>
        <p style={{ wordBreak: 'break-all' }}>{game.fen()}</p>
      </div>
    </div>
  );
};

export default ChessGame;