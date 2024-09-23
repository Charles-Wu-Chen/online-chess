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
from best_line import BestLine  # Import the BestLine class
import asyncio

app = Flask(__name__)
CORS(app, resources={r"/evaluate": {"origins": "http://localhost:3000"}, 
                     r"/evaluation-result": {"origins": "http://localhost:3000"},
                     r"/sharpness": {"origins": "http://localhost:3000"},
                     r"/sharpness-result": {"origins": "http://localhost:3000"},
                     r"/best-lines": {"origins": "http://localhost:3000"},
                     r"/best-lines-result": {"origins": "http://localhost:3000"}})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
sf: Optional[ChessEngine] = None
leela: Optional[ChessEngine] = None

# Stockfish configuration
stockfish_path = os.environ.get('STOCKFISH_PATH', r'K:\github\stockfish-windows-x86-64\stockfish\stockfish-windows-x86-64.exe')
stockfish_options = {'Threads': '10', 'Hash': '4096'}

# Leela Chess Zero configuration
leela_path = r'K:\leela\lc0-v0.30.0-windows-gpu-nvidia-cudnn\lc0.exe'
weights_path = r'K:\leela\lc0-v0.30.0-windows-gpu-nvidia-cudnn\791556.pb.gz'
leela_options = {'WeightsFile': weights_path, 'UCI_ShowWDL': 'true'}

evaluation_queue = queue.Queue(maxsize=1)
evaluation_thread = None
evaluation_lock = threading.Lock()
latest_evaluation = None

sharpness_queue = queue.Queue(maxsize=1)
sharpness_thread = None
sharpness_lock = threading.Lock()
latest_sharpness = None

best_lines_queue = queue.Queue(maxsize=1)
best_lines_thread = None
best_lines_lock = threading.Lock()
latest_best_lines = None

engine_lock = threading.Lock()

def initialize_engines():
    global sf, leela
    
    with engine_lock:
        if sf is None:
            try:
                sf = create_engine("stockfish", stockfish_path, stockfish_options)
                logger.info("Stockfish engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Stockfish engine: {str(e)}")
                logger.error(traceback.format_exc())
        
        if leela is None:
            try:
                leela = create_engine("leela", leela_path, leela_options)
                logger.info("Leela Chess Zero engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Leela Chess Zero engine: {str(e)}")
                logger.error(traceback.format_exc())

def restart_engine(engine_name: str):
    global sf, leela
    with engine_lock:
        if engine_name == "stockfish":
            if sf:
                try:
                    sf.quit()
                except Exception as e:
                    logger.error(f"Error shutting down Stockfish engine: {str(e)}")
            sf = None
            try:
                sf = create_engine("stockfish", stockfish_path, stockfish_options)
                logger.info("Stockfish engine restarted successfully")
            except Exception as e:
                logger.error(f"Failed to restart Stockfish engine: {str(e)}")
                logger.error(traceback.format_exc())
        elif engine_name == "leela":
            if leela:
                try:
                    leela.quit()
                except Exception as e:
                    logger.error(f"Error shutting down Leela Chess Zero engine: {str(e)}")
            leela = None
            try:
                leela = create_engine("leela", leela_path, leela_options)
                logger.info("Leela Chess Zero engine restarted successfully")
            except Exception as e:
                logger.error(f"Failed to restart Leela Chess Zero engine: {str(e)}")
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
            restart_engine("stockfish")
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

@app.route('/evaluation-result', methods=['GET'])
def get_evaluation_result():
    with evaluation_lock:
        if latest_evaluation is not None:
            return jsonify({"status": "completed", "evaluation": latest_evaluation})
        else:
            return jsonify({"status": "in_progress"})

def sharpness_calculation_thread():
    global leela, latest_sharpness
    while True:
        try:
            fen = sharpness_queue.get()
            if fen is None:  # Signal to stop the thread
                break
            
            with sharpness_lock:
                if leela is None:
                    initialize_engines()
                
                board = chess.Board(fen)
                result = leela.analyse(board, Limit(time=1.0))
                wdl = result.get("wdl")
                
                if wdl is None:
                    latest_sharpness = None
                else:
                    sharpness = sharpnessLC0(wdl)
                    latest_sharpness = sharpness
                    logger.info(f"Sharpness calculation complete. Sharpness: {sharpness}")
        except Exception as e:
            logger.error(f"Error during sharpness calculation: {str(e)}")
            logger.error(traceback.format_exc())
            latest_sharpness = None
            restart_engine("leela")
        finally:
            sharpness_queue.task_done()

@app.route('/sharpness', methods=['POST'])
def calculate_sharpness():
    global sharpness_thread
    
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

    # Clear the queue and add the new request
    while not sharpness_queue.empty():
        try:
            sharpness_queue.get_nowait()
        except queue.Empty:
            break
    sharpness_queue.put(fen)

    # Start the sharpness thread if it's not running
    if sharpness_thread is None or not sharpness_thread.is_alive():
        sharpness_thread = threading.Thread(target=sharpness_calculation_thread)
        sharpness_thread.start()

    return jsonify({"message": "Sharpness calculation request received"}), 202

@app.route('/sharpness-result', methods=['GET'])
def get_sharpness_result():
    with sharpness_lock:
        if latest_sharpness is not None:
            return jsonify({"status": "completed", "sharpness": latest_sharpness})
        else:
            return jsonify({"status": "in_progress"})

def sharpnessLC0(wdl: list) -> float:
    W = min(max(wdl[0]/1000, 0.0001), 0.9999)
    L = min(max(wdl[2]/1000, 0.0001), 0.9999)
    return (max(2/(np.log((1/W)-1) + np.log((1/L)-1)), 0))**2 * min(W, L) * 4

def best_lines_calculation_thread():
    global sf, leela, latest_best_lines
    while True:
        try:
            current_fen, number_of_lines, depth = best_lines_queue.get()
            if current_fen is None:  # Signal to stop the thread
                break
            
            with engine_lock:
                if sf is None or leela is None:
                    initialize_engines()

                board = chess.Board(current_fen)
                info = sf.analyse_with_multipv(board, chess.engine.Limit(depth=depth), multipv=number_of_lines)
                best_lines = []

                for i, line_info in enumerate(info):
                    logger.info(f"Line {i+1}:")
                    moves = line_info['pv']
                    move_sans = board.variation_san(moves)
                    score = line_info['score'].relative.score()
                    logger.info(f"Moves: {move_sans}, Score: {score}")

                    # Generate the FEN based on the next move
                    board.push(moves[0])
                    new_fen = board.fen()
                    board.pop()

                    try:
                        leela_board = chess.Board(new_fen)
                        wdl_info = leela.analyse(leela_board, Limit(time=1.0))
                        wdl = wdl_info['wdl']
                    except chess.engine.EngineTerminatedError as e:
                        logger.error(f"Leela engine terminated unexpectedly: {str(e)}")
                        leela = None  # Reset the engine
                        restart_engine("leela")
                        raise
                    except Exception as e:
                        logger.error(f"Error during Leela analysis: {str(e)}")
                        logger.error(traceback.format_exc())
                        restart_engine("leela")
                        raise

                    # Calculate the sharpness based on WDL
                    sharpness = sharpnessLC0(wdl)
                    logger.info(f"Sharpness: {sharpness}")

                    # Append the best line with sharpness
                    best_line = BestLine(move_sans, score, sharpness)
                    best_lines.append(best_line.to_dict())

                with best_lines_lock:
                    latest_best_lines = best_lines
                logger.info("Best lines calculation complete")
        except Exception as e:
            logger.error(f"Error during best lines calculation: {str(e)}")
            logger.error(traceback.format_exc())
            with best_lines_lock:
                latest_best_lines = None
        finally:
            best_lines_queue.task_done()

@app.route('/best-lines', methods=['POST'])
def get_best_lines():
    global best_lines_thread
    
    if not request.is_json:
        logger.warning("Request Content-Type is not application/json")
        return jsonify({"error": "Content-Type must be application/json"}), 415

    try:
        data = request.json
    except UnsupportedMediaType:
        logger.warning("Failed to parse JSON data")
        return jsonify({"error": "Invalid JSON data"}), 400

    current_fen = data.get('current_fen')
    number_of_lines = data.get('number_of_lines', 1)
    depth = data.get('depth', 20)

    if not current_fen:
        logger.warning("FEN string not provided in request")
        return jsonify({"error": "FEN string is required"}), 400

    logger.info(f"Getting best lines: FEN={current_fen}, number_of_lines={number_of_lines}, depth={depth}")

    # Clear the queue and add the new request
    while not best_lines_queue.empty():
        try:
            best_lines_queue.get_nowait()
        except queue.Empty:
            break
    best_lines_queue.put((current_fen, number_of_lines, depth))

    # Start the best lines thread if it's not running
    if best_lines_thread is None or not best_lines_thread.is_alive():
        best_lines_thread = threading.Thread(target=best_lines_calculation_thread)
        best_lines_thread.start()

    return jsonify({"message": "Best lines calculation request received"}), 202

@app.route('/best-lines-result', methods=['GET'])
def get_best_lines_result():
    with best_lines_lock:
        if latest_best_lines is not None:
            return jsonify({"status": "completed", "best_lines": latest_best_lines})
        else:
            return jsonify({"status": "in_progress"})


if __name__ == '__main__':
    logger.info("Starting Flask application")
    initialize_engines()  # Initialize engines when the app starts
    app.run(host='0.0.0.0', debug=True, threaded=True)