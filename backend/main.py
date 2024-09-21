from flask import Flask, request, jsonify, after_this_request
from flask_cors import CORS
import chess
from chess.engine import Limit
from typing import Optional
import os
import traceback
import logging
from werkzeug.exceptions import UnsupportedMediaType
import threading
import queue
import numpy as np
from chess_engines import create_engine, ChessEngine

app = Flask(__name__)
CORS(app, resources={r"/evaluate": {"origins": "http://localhost:3000"}, 
                     r"/evaluation-result": {"origins": "http://localhost:3000"},
                     r"/sharpness": {"origins": "http://localhost:3000"}})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
sf: Optional[ChessEngine] = None
leela: Optional[ChessEngine] = None
evaluation_queue = queue.Queue(maxsize=1)
evaluation_thread = None
evaluation_lock = threading.Lock()
latest_evaluation = None

engine_lock = threading.Lock()
engines_initialized = False

def initialize_engines():
    global engines_initialized, sf, leela
    
    with engine_lock:
        if not engines_initialized:
            try:
                stockfish_path = os.environ.get('STOCKFISH_PATH', r'K:\github\stockfish-windows-x86-64\stockfish\stockfish-windows-x86-64.exe')
                stockfish_options = {'Threads': '10', 'Hash': '4096'}
                sf = create_engine("stockfish", stockfish_path, stockfish_options)

                leela_path = r'K:\leela\lc0-v0.30.0-windows-gpu-nvidia-cudnn\lc0.exe'
                weights_path = r'K:\leela\lc0-v0.30.0-windows-gpu-nvidia-cudnn\791556.pb.gz'
                leela_options = {'WeightsFile': weights_path, 'UCI_ShowWDL': 'true'}
                leela = create_engine("leela", leela_path, leela_options)

                logger.info("Stockfish and Leela Chess Zero engines initialized successfully")
                engines_initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize chess engines: {str(e)}")
                logger.error(traceback.format_exc())

def evaluate_position_thread():
    global sf, latest_evaluation
    while True:
        try:
            fen, depth = evaluation_queue.get()
            if fen is None:  # Signal to stop the thread
                break
            
            with evaluation_lock:
                if sf is None:
                    initialize_engines()
                
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

# Add this new route
@app.route('/sharpness', methods=['POST'])
def get_sharpness():
    global leela
    
    if not request.is_json:
        logger.warning("Request Content-Type is not application/json")
        return jsonify({"error": "Content-Type must be application/json"}), 415

    try:
        data = request.json
    except UnsupportedMediaType:
        logger.warning("Failed to parse JSON data")
        return jsonify({"error": "Invalid JSON data"}), 400

    fen = data.get('fen')

    if not fen:
        logger.warning("FEN string not provided in request")
        return jsonify({"error": "FEN string is required"}), 400

    logger.info(f"Calculating sharpness for position: FEN={fen}")

    try:
        if leela is None:
            leela_path = r'K:\leela\lc0-v0.30.0-windows-gpu-nvidia-cudnn\lc0.exe'
            weights_path = r'K:\leela\lc0-v0.30.0-windows-gpu-nvidia-cudnn\791556.pb.gz'
            leela_options = {'WeightsFile': weights_path, 'UCI_ShowWDL': 'true'}
            leela = create_engine("leela", leela_path, leela_options)
            logger.info("Leela Chess Zero engine initialized for sharpness calculation")
        
        board = chess.Board(fen)
        result = leela.analyse(board, Limit(time=1.0))
        wdl = result.get("wdl")
        
        if wdl is None:
            return jsonify({"error": "Failed to get WDL from Leela Chess Zero"}), 500
        
        sharpness = sharpnessLC0(wdl)
        logger.info(f"Sharpness calculation complete. Sharpness: {sharpness}")
        
        @after_this_request
        def shutdown_leela(response):
            global leela
            try:
                logger.info("Shutting down Leela Chess Zero engine")
                leela.quit()
                logger.info("Leela Chess Zero engine shut down successfully")
            except Exception as e:
                logger.error(f"Error shutting down Leela Chess Zero engine: {str(e)}")
            finally:
                leela = None
            return response

        return jsonify({"sharpness": sharpness}), 200
    except Exception as e:
        logger.error(f"Error during sharpness calculation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

def sharpnessLC0(wdl: list) -> float:
    W = min(max(wdl[0]/1000, 0.0001), 0.9999)
    L = min(max(wdl[2]/1000, 0.0001), 0.9999)
    return (max(2/(np.log((1/W)-1) + np.log((1/L)-1)), 0))**2 * min(W, L) * 4

@app.teardown_appcontext
def shutdown_engine(exception=None):
    global sf, leela, evaluation_thread
    
    # Stop the evaluation thread
    if evaluation_thread and evaluation_thread.is_alive():
        evaluation_queue.put((None, None))  # Signal to stop the thread
        evaluation_thread.join(timeout=5)
    
    with evaluation_lock:
        if sf:
            try:
                logger.info("Shutting down Stockfish engine")
                sf.quit()
                logger.info("Stockfish engine shut down successfully")
            except Exception as e:
                logger.error(f"Error shutting down Stockfish engine: {str(e)}")
            finally:
                sf = None

if __name__ == '__main__':
    logger.info("Starting Flask application")
    initialize_engines()  # Initialize engines when the app starts
    app.run(host='0.0.0.0', debug=True, threaded=True)