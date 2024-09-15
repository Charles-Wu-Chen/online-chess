import React, { forwardRef, useEffect, useRef, useState, useMemo } from "react";
import { Chess } from "chess.js";

import {
  Chessboard,
  ClearPremoves,
  SparePiece,
  ChessboardDnDProvider,
} from "react-chessboard";


const buttonStyle = {
    cursor: "pointer",
    padding: "10px 20px",
    margin: "10px 10px 0px 0px",
    borderRadius: "6px",
    backgroundColor: "#f0d9b5",
    border: "none",
    boxShadow: "0 2px 5px rgba(0, 0, 0, 0.5)",
  };
  
  const inputStyle = {
    padding: "10px 20px",
    margin: "10px 0 10px 0",
    borderRadius: "6px",
    border: "none",
    boxShadow: "0 2px 5px rgba(0, 0, 0, 0.5)",
    width: "100%",
  };
  
  const boardWrapper = {
    width: `70vw`,
    maxWidth: "70vh",
    margin: "3rem auto",
  };

  
const App = () => {
    const [game, setGame] = useState(new Chess());
    const [currentTimeout, setCurrentTimeout] = useState();
    const [isCheckmate, setIsCheckmate] = useState(false);

    function safeGameMutate(modify) {
      setGame((g) => {
        const update = new Chess(g.fen());
        modify(update);
        return update;
      });
    }
    function makeRandomMove() {
      safeGameMutate(game => {
        const possibleMoves = game.moves();
        if (game.isGameOver() || game.isDraw() || possibleMoves.length === 0) return;
        const randomIndex = Math.floor(Math.random() * possibleMoves.length);
        game.move(possibleMoves[randomIndex]);
        updateGameState(game);
      });
    }

    function updateGameState(newGame) {
      setGame(newGame);
      setIsCheckmate(newGame.isCheckmate());
    }

    function onDrop(sourceSquare, targetSquare, piece) {
        try {
            const gameCopy = new Chess(game.fen());
            const move = gameCopy.move({
                from: sourceSquare,
                to: targetSquare,
                promotion: piece[1].toLowerCase() ?? "q",
            });

            // illegal move
            if (move === null) return false;

            // If we reach here, the move was successful
            updateGameState(gameCopy);

            // store timeout so it can be cleared on undo/reset so computer doesn't execute move
            if (!gameCopy.isGameOver()) {
                const newTimeout = setTimeout(makeRandomMove, 200);
                setCurrentTimeout(newTimeout);
            }
            return true;
        } catch (error) {
            console.error("Error in onDrop:", error);
            return false;
        }
    }

    return <div style={boardWrapper}>
        <ChessboardDnDProvider>
          <Chessboard id="PlayVsRandom" position={game.fen()} onPieceDrop={onDrop} boardWidth={400}/>
        </ChessboardDnDProvider>
        {isCheckmate && <div style={{ marginTop: '20px', fontWeight: 'bold' }}>Checkmate!</div>}
        <button style={buttonStyle} onClick={() => {
        safeGameMutate(game => {
          game.reset();
        });
        clearTimeout(currentTimeout);
        setIsCheckmate(false);
      }}>
          reset
        </button>
        <button style={buttonStyle} onClick={() => {
        safeGameMutate(game => {
          game.undo();
        });
        clearTimeout(currentTimeout);
        updateGameState(game);
      }}>
          undo
        </button>
      </div>;
  } 

  export default App;