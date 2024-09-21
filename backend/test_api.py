import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"

def test_home_endpoint():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert "Welcome to the Chess Analysis API" in response.text
    logger.info("Home endpoint test passed")

def test_evaluate_endpoint():
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    data = {"fen": fen, "depth": 10}
    response = requests.post(f"{BASE_URL}/evaluate", json=data)
    assert response.status_code == 202
    assert "Evaluation request received" in response.json()["message"]
    logger.info("Evaluate endpoint test passed")

def test_evaluation_result_endpoint():
    max_attempts = 30
    for _ in range(max_attempts):
        response = requests.get(f"{BASE_URL}/evaluation-result")
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "completed":
            assert "evaluation" in data
            logger.info("Evaluation result endpoint test passed")
            return
        time.sleep(1)
    assert False, "Evaluation result not received within the expected time"

def test_sharpness_endpoint():
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    data = {"fen": fen}
    response = requests.post(f"{BASE_URL}/sharpness", json=data)
    assert response.status_code == 202
    assert "Sharpness calculation request received" in response.json()["message"]
    logger.info("Sharpness endpoint test passed")

def test_sharpness_result_endpoint():
    max_attempts = 30
    for _ in range(max_attempts):
        response = requests.get(f"{BASE_URL}/sharpness-result")
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "completed":
            assert "sharpness" in data
            logger.info("Sharpness result endpoint test passed")
            return
        time.sleep(1)
    assert False, "Sharpness result not received within the expected time"

def run_all_tests():
    try:
        test_home_endpoint()
        test_evaluate_endpoint()
        test_evaluation_result_endpoint()
        test_sharpness_endpoint()
        test_sharpness_result_endpoint()
        logger.info("All tests passed successfully!")
    except AssertionError as e:
        logger.error(f"Test failed: {str(e)}")
    except Exception as e:
        logger.error(f"An error occurred during testing: {str(e)}")

if __name__ == "__main__":
    run_all_tests()