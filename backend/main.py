from flask import Flask, request, jsonify, render_template
import chess
import chess.engine
from typing import Dict, Any
import os
import traceback
import logging
from werkzeug.exceptions import UnsupportedMediaType

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global variable for the engine
sf = None

def create_engine():
    global sf
    engine_path = os.environ.get('STOCKFISH_PATH', r'K:\github\stockfish-windows-x86-64\stockfish\stockfish-windows-x86-64.exe')
    try:
        sf = configureEngine(engine_path, {'Threads': '10', 'Hash': '4096'})
        logger.info(f"Stockfish engine initialized successfully at {engine_path}")
    except Exception as e:
        logger.error(f"Failed to initialize Stockfish engine: {str(e)}")
        logger.error(traceback.format_exc())

def configureEngine(engineName: str, uci_options: Dict[str, str]) -> chess.engine.SimpleEngine:
    """
    Configure a chess engine with the given UCI options and return the engine.
    """
    eng = chess.engine.SimpleEngine.popen_uci(engineName)
    eng.configure(uci_options)
    return eng

@app.route('/evaluate', methods=['POST'])
def evaluate_position():
    global sf
    if sf is None:
        create_engine()  # Ensure engine is created if it doesn't exist

    if not request.is_json:
        logger.warning("Request Content-Type is not application/json")
        return jsonify({"error": "Content-Type must be application/json"}), 415

    try:
        data = request.json
    except UnsupportedMediaType:
        logger.warning("Failed to parse JSON data")
        return jsonify({"error": "Invalid JSON data"}), 400

    fen = data.get('fen')
    depth = data.get('depth', 20)

    if not fen:
        logger.warning("FEN string not provided in request")
        return jsonify({"error": "FEN string is required"}), 400

    try:
        board = chess.Board(fen)
        result = sf.analyse(board, chess.engine.Limit(depth=depth))
        evaluation = result["score"].relative.score(mate_score=100000)
        return jsonify({"evaluation": evaluation})
    except chess.engine.EngineTerminatedError as e:
        logger.error(f"Engine terminated unexpectedly: {str(e)}")
        logger.error(traceback.format_exc())
        create_engine()  # Recreate the engine if it crashed
        return jsonify({"error": "Engine error, please try again"}), 500
    except Exception as e:
        logger.error(f"Error during position evaluation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 400

@app.route('/')
def home():
    return "Welcome to the Chess Analysis API"

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    logger.error(traceback.format_exc())
    return jsonify({"error": "An unexpected error occurred"}), 500

@app.errorhandler(UnsupportedMediaType)
def handle_unsupported_media_type(e):
    logger.warning(f"Unsupported Media Type: {str(e)}")
    return jsonify({"error": "Unsupported Media Type. Use application/json"}), 415

# Call the function to configure the engine when the app starts
create_engine()

@app.teardown_appcontext
def shutdown_engine(exception=None):
    global sf
    if sf:
        sf.quit()
        sf = None
        logger.info("Stockfish engine shut down")

if __name__ == '__main__':
    create_engine()  # Ensure engine is created when the app starts
    app.run(host='0.0.0.0', debug=True)