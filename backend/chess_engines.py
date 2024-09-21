import chess
import chess.engine
from typing import Dict

class ChessEngine:
    def __init__(self, engine_path: str, options: Dict[str, str]):
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.engine.configure(options)

    def analyse(self, board: chess.Board, limit: chess.engine.Limit):
        return self.engine.analyse(board, limit)

    def quit(self):
        self.engine.quit()

class StockfishEngine(ChessEngine):
    def __init__(self, engine_path: str, options: Dict[str, str]):
        super().__init__(engine_path, options)

class LeelaEngine(ChessEngine):
    def __init__(self, engine_path: str, options: Dict[str, str]):
        super().__init__(engine_path, options)

def create_engine(engine_type: str, engine_path: str, options: Dict[str, str]) -> ChessEngine:
    if engine_type == "stockfish":
        return StockfishEngine(engine_path, options)
    elif engine_type == "leela":
        return LeelaEngine(engine_path, options)
    else:
        raise ValueError(f"Unsupported engine type: {engine_type}")