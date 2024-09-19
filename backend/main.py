from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import chess.engine
from typing import Dict, Any
import os
import traceback
import logging
from werkzeug.exceptions import UnsupportedMediaType
import threading
import queue

app = Flask(__name__)
CORS(app, resources={r"/evaluate": {"origins": "http://localhost:3000"}, r"/evaluation-result": {"origins": "http://localhost:3000"}})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
sf = None
evaluation_queue = queue.Queue(maxsize=1)
evaluation_thread = None
evaluation_lock = threading.Lock()
latest_evaluation = None

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

def evaluate_position_thread():
    global sf, latest_evaluation
    while True:
        try:
            fen, depth = evaluation_queue.get()
            if fen is None:  # Signal to stop the thread
                break
            
            with evaluation_lock:
                if sf is None:
                    create_engine()
                
                board = chess.Board(fen)
                result = sf.analyse(board, chess.engine.Limit(depth=depth))
                evaluation = result["score"].relative.score(mate_score=100000)
                latest_evaluation = evaluation
                logger.info(f"Analysis complete. Evaluation: {evaluation}")
        except Exception as e:
            logger.error(f"Error during position evaluation: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            evaluation_queue.task_done()

@app.route('/evaluate', methods=['POST'])
def evaluate_position():
    global evaluation_thread
    
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

    logger.info(f"Evaluating position: FEN={fen}, depth={depth}")

    # Clear the queue and add the new request
    while not evaluation_queue.empty():
        try:
            evaluation_queue.get_nowait()
        except queue.Empty:
            break
    evaluation_queue.put((fen, depth))

    # Start the evaluation thread if it's not running
    if evaluation_thread is None or not evaluation_thread.is_alive():
        evaluation_thread = threading.Thread(target=evaluate_position_thread)
        evaluation_thread.start()

    return jsonify({"message": "Evaluation request received"}), 202

@app.route('/')
def home():
    logger.info("Home route accessed")
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

# Add this new route
@app.route('/evaluation-result', methods=['GET'])
def get_evaluation_result():
    with evaluation_lock:
        if latest_evaluation is not None:
            return jsonify({"status": "completed", "evaluation": latest_evaluation})
        else:
            return jsonify({"status": "in_progress"})

# Call the function to configure the engine when the app starts
logger.info("Initializing Stockfish engine")
create_engine()

@app.teardown_appcontext
def shutdown_engine(exception=None):
    global sf, evaluation_thread
    
    # Stop the evaluation thread
    if evaluation_thread and evaluation_thread.is_alive():
        evaluation_queue.put((None, None))  # Signal to stop the thread
        evaluation_thread.join(timeout=5)
    
    with evaluation_lock:
        if sf:
            logger.info("Shutting down Stockfish engine")
            sf.quit()
            sf = None
            logger.info("Stockfish engine shut down successfully")

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', debug=True, threaded=True)