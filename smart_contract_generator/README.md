# Smart Contract Generator API

## Description

This microservice provides a FastAPI-based API to generate Solidity smart contracts, starting with ERC20 tokens. It also offers placeholder endpoints for related smart contract services.

## Prerequisites

*   Python 3.12 or higher.

## Setup & Installation

1.  **Clone the repository:**
    (This step is generally done by your version control system if you're cloning an existing project)
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Navigate to the project directory:**
    If you've just cloned, you're likely already there. The root directory is `smart_contract_generator`.

3.  **Create a virtual environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python -m venv venv
    ```

4.  **Activate the virtual environment:**
    *   **Windows:**
        ```bash
        venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

5.  **Install dependencies:**
    Install all the required packages listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

## Running the Service

To run the FastAPI application using Uvicorn (a fast ASGI server):

```bash
uvicorn smart_contract_generator.app.main:app --reload
```

*   `smart_contract_generator.app.main:app` refers to the `app` instance of FastAPI in the `main.py` file within the `smart_contract_generator/app` module.
*   `--reload` enables auto-reloading when code changes are detected, which is useful for development.

The API will typically be available at `http://127.0.0.1:8000`.

## API Endpoints

### `GET /`

*   **Description:** Root endpoint, returns a welcome message.
*   **Response:**
    ```json
    {
      "message": "Smart Contract Generator API"
    }
    ```

### `POST /generate/erc20/`

*   **Description:** Generates the Solidity code for a basic ERC20 token.
*   **Request Body (JSON):**
    ```json
    {
      "name": "My Test Token",
      "symbol": "MTT",
      "initial_supply": 1000000,
      "decimals": 18
    }
    ```
    *   `name`: (string) The name of the token.
    *   `symbol`: (string) The symbol/ticker of the token.
    *   `initial_supply`: (integer) The total number of tokens to be minted initially (raw amount, not adjusted for decimals).
    *   `decimals`: (integer, optional, default: 18) The number of decimal places the token will support.

*   **Response (JSON):**
    ```json
    {
      "solidity_code": "pragma solidity ^0.8.0; contract MyTestToken { /* ... rest of the contract code ... */ }"
    }
    ```

### `POST /service/prepare-contract-interaction/`

*   **Description:** Placeholder service to simulate preparing data for a smart contract function call.
*   **Request Body (JSON):**
    ```json
    {
      "contract_address": "0x123abc0000000000000000000000000000000000",
      "function_name": "transfer",
      "args": ["0xdef4560000000000000000000000000000000000", 100]
    }
    ```
    *   `contract_address`: (string) The Ethereum address of the smart contract.
    *   `function_name`: (string) The name of the contract function to be called.
    *   `args`: (list) A list of arguments for the function.

*   **Response (JSON):**
    ```json
    {
      "data": {
        "action": "prepare_contract_interaction",
        "contract_address": "0x123abc0000000000000000000000000000000000",
        "function_name": "transfer",
        "arguments": ["0xdef4560000000000000000000000000000000000", 100],
        "note": "This is a placeholder. Actual data preparation would involve ABI encoding."
      }
    }
    ```

## Running Tests

To discover and run all unit tests located in the `smart_contract_generator/tests` directory, execute the following command from the project's root directory (`smart_contract_generator/`):

```bash
python -m unittest discover -s smart_contract_generator/tests
```

Alternatively, if your current working directory is the root of the project, you might be able to use a simpler command if the test structure is standard:

```bash
python -m unittest
```
