import unittest
import os
import sys
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app # Import the FastAPI app instance

class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Smart Contract Generator API"})

    def test_generate_erc20_success(self):
        payload = {
            "name": "TestAPIToken",
            "symbol": "TAPT",
            "initial_supply": 10000,
            "decimals": 18
        }
        response = self.client.post("/generate/erc20/", json=payload)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertIn("solidity_code", json_response)
        self.assertIsInstance(json_response["solidity_code"], str)
        self.assertTrue(len(json_response["solidity_code"]) > 0)
        self.assertIn(f"contract {payload['name']}", json_response["solidity_code"])
        self.assertIn(f'string public symbol = "{payload["symbol"]}";', json_response["solidity_code"])
        expected_adjusted_supply = payload["initial_supply"] * (10**payload["decimals"])
        self.assertIn(f"totalSupply = {expected_adjusted_supply};", json_response["solidity_code"])


    def test_generate_erc20_invalid_input_missing_name(self):
        payload = {
            # name is missing
            "symbol": "TAPT",
            "initial_supply": 10000
        }
        response = self.client.post("/generate/erc20/", json=payload)
        self.assertEqual(response.status_code, 422) # Unprocessable Entity

    def test_generate_erc20_invalid_input_wrong_type(self):
        payload = {
            "name": "TestAPIToken",
            "symbol": "TAPT",
            "initial_supply": "not_an_integer" # wrong type
        }
        response = self.client.post("/generate/erc20/", json=payload)
        self.assertEqual(response.status_code, 422) # Unprocessable Entity


    def test_prepare_contract_interaction_success(self):
        payload = {
            "contract_address": "0x123abc",
            "function_name": "transfer",
            "args": ["0x456def", 100]
        }
        response = self.client.post("/service/prepare-contract-interaction/", json=payload)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertIn("data", json_response)
        expected_data = {
            "action": "prepare_contract_interaction",
            "contract_address": payload["contract_address"],
            "function_name": payload["function_name"],
            "arguments": payload["args"],
            "note": "This is a placeholder. Actual data preparation would involve ABI encoding."
        }
        self.assertEqual(json_response["data"], expected_data)

    def test_prepare_contract_interaction_invalid_input(self):
        payload = {
            # contract_address is missing
            "function_name": "transfer",
            "args": ["0x456def", 100]
        }
        response = self.client.post("/service/prepare-contract-interaction/", json=payload)
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
