# Chess Analysis API with Stockfish

This project is a Flask-based API that uses the Stockfish chess engine to analyze chess positions and provide various chess-related features.

## Prerequisites

- Python 3.7 or higher
- Anaconda or Miniconda
- Stockfish chess engine (Windows x86-64 version)

## Setup

1. Clone the repository:
   ```bash
   git clone <your-repository-url>
   cd <your-project-directory>
   ```

2. Create a Conda environment:
   ```bash
   conda create --name online-chess-backend python=3.11
   ```

3. Activate the Conda environment:
   ```bash
   conda activate online-chess-backend
   ```
   Deactive the conda environment
   ```bash
   conda deactivate
   ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Download Stockfish:
   - Download the Stockfish engine for Windows x86-64 from the official website: https://stockfishchess.org/download/
   - Extract the downloaded file and note the path to the `stockfish-windows-x86-64.exe` file

6. Update the Stockfish path in `backend/main.py`:
   - Open `backend/main.py` in a text editor
   - Locate the `create_engine()` function
   - Update the path to match your Stockfish executable location:
     ```python
     engine_path = os.environ.get('STOCKFISH_PATH', r'path\to\your\stockfish-windows-x86-64.exe')
     ```

## Running the Server

1. Ensure you're in the project directory and your Conda environment is activated:
   ```bash
   conda activate online-chess-backend
   ```

2. Start the Flask development server:
   ```bash
   python main.py
   ```

3. The server should now be running on `http://127.0.0.1:5000/`

## API Usage

### Root Endpoint

- Endpoint: `/`
- Method: GET
- Response: A welcome message
- Curl command:
  ```bash
  curl http://127.0.0.1:5000/
  ```
  in wsl curl command:
  ```bash
  curl http://host.docker.internal:5000
  ```

### Evaluate Position

- Endpoint: `/evaluate`
- Method: POST
- Request Body:
  ```json
  {
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "depth": 20
  }
  ```
- Response:
  ```json
  {
    "message": "Evaluation request received"
  }
  ```
- Status Code: 202 (Accepted)
- Curl command:
  ```bash
  curl -X POST http://host.docker.internal:5000/evaluate \
       -H "Content-Type: application/json" \
       -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "depth": 20}'
  ```

### Get Evaluation Result

- Endpoint: `/evaluation-result`
- Method: GET
- Response:
  - If evaluation is complete:
    ```json
    {
      "status": "completed",
      "evaluation": 10
    }
    ```
  - If evaluation is still in progress:
    ```json
    {
      "status": "in_progress"
    }
    ```
- Curl command:
  ```bash
  curl http://127.0.0.1:5000/evaluation-result
  ```

Note: After submitting an evaluation request to `/evaluate`, you should poll the `/evaluation-result` endpoint to get the final evaluation. The evaluation value represents the position's score in centipawns (100 centipawns = 1 pawn advantage).

### Calculate Position Sharpness

- Endpoint: `/sharpness`
- Method: POST
- Request Body:
  ```json
  {
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
  }
  ```
- Response:
  ```json
  {
    "message": "Sharpness calculation request received"
  }
  ```
- Status Code: 202 (Accepted)
- Curl command:
  ```bash
  curl -X POST http://host.docker.internal:5000/sharpness \
       -H "Content-Type: application/json" \
       -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}'
  ```

### Get Sharpness Result

- Endpoint: `/sharpness-result`
- Method: GET
- Response:
  - If sharpness calculation is complete:
    ```json
    {
      "status": "completed",
      "sharpness": 0.5
    }
    ```
  - If sharpness calculation is still in progress:
    ```json
    {
      "status": "in_progress"
    }
    ```
- Curl command:
  ```bash
  curl http://host.docker.internal:5000/sharpness-result
  ```

Note: After submitting a sharpness calculation request to `/sharpness`, you should poll the `/sharpness-result` endpoint to get the final sharpness value. The sharpness value is a non-negative float, where higher values indicate a sharper position. This endpoint uses the Leela Chess Zero engine to calculate the position's sharpness based on the WDL (Win-Draw-Loss) probabilities.

### Get Best Lines

- Endpoint: `/best-lines`
- Method: POST
- Request Body:
  ```json
  {
    "current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "number_of_lines": 3,
    "depth": 20
  }
  ```
- Response:
  ```json
  {
    "message": "Best lines calculation request received"
  }
  ```
- Status Code: 202 (Accepted)
- Curl command:
  ```bash
  curl -X POST http://host.docker.internal:5000/best-lines \
       -H "Content-Type: application/json" \
       -d '{"current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "number_of_lines": 3, "depth": 20}'
  ```

### Get Best Lines Result

- Endpoint: `/best-lines-result`
- Method: GET
- Response:
  - If best lines calculation is complete:
    ```json
    {
      "status": "completed",
      "best_lines": [
        {
          "moves": "e4 e5 Nf3 Nc6 Bb5",
          "score": 35,
          "sharpness": 0.1234
        },
        {
          "moves": "d4 d5 c4 c6 Nc3",
          "score": 30,
          "sharpness": 0.2345
        },
        {
          "moves": "Nf3 d5 g3 Nf6 Bg2",
          "score": 25,
          "sharpness": 0.3456
        }
      ]
    }
    ```
  - If best lines calculation is still in progress:
    ```json
    {
      "status": "in_progress"
    }
    ```
- Curl command:
  ```bash
  curl http://host.docker.internal:5000/best-lines-result
  ```

Note: The `score` is in centipawns (100 centipawns = 1 pawn advantage). The `sharpness` is a float value between 0 and +infinity, where higher values indicate a sharper position.

## Adding New Features

To add new Stockfish features:

1. Open `main.py`
2. Add new route functions using the `@app.route` decorator
3. Implement the feature using the `sf` Stockfish engine object
4. If you add new dependencies, make sure to update the `requirements.txt` file:
   ```bash
   pip freeze > requirements.txt
   ```

## Troubleshooting

- If you encounter any issues with the Stockfish engine, ensure that the path to the executable is correct and that you have the right version for your system.
- Make sure all dependencies are installed correctly within your Conda environment.
- If you're having issues with the Conda environment, try recreating it:
  ```bash
  conda deactivate
  conda remove --name chess-api --all
  conda create --name chess-api python=3.9
  conda activate chess-api
  pip install -r requirements.txt
  ```

- If you see a "Welcome to the Chess Analysis API" message when accessing the root URL (http://127.0.0.1:5000/), the server is running correctly.
- For any "Not found" errors, make sure you're using the correct endpoint URL.

## Contributing

Feel free to submit issues or pull requests if you have suggestions for improvements or encounter any bugs.

## License

[Your chosen license]