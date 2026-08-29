import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.contract_generator import ERC20ContractGenerator


class TestERC20ContractGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ERC20ContractGenerator()

    def test_generate_contract_valid_inputs(self):
        name = "TestToken"
        symbol = "TTT"
        initial_supply = 1000
        decimals = 18
        expected_adjusted_supply = initial_supply * (10**decimals)

        code = self.generator.generate_contract(name, symbol, initial_supply, decimals)

        self.assertIn(f"contract {name}", code)
        self.assertIn(f'string public name = "{name}";', code)
        self.assertIn(f'string public symbol = "{symbol}";', code)
        self.assertIn(f"uint8 public decimals = {decimals};", code)
        self.assertIn(f"totalSupply = {expected_adjusted_supply};", code)
        self.assertIn(f"balanceOf[msg.sender] = {expected_adjusted_supply};", code)

        # Check for essential public state and function signatures
        # Solidity public variables generate getters (name(), symbol(), etc.)
        self.assertIn("string public name", code)
        self.assertIn("string public symbol", code)
        self.assertIn("uint8 public decimals", code)
        self.assertIn("uint256 public totalSupply", code)
        self.assertIn("mapping(address => uint256) public balanceOf", code)
        self.assertIn(
            "mapping(address => mapping(address => uint256)) public allowance", code
        )
        self.assertIn("function transfer(address to, uint256 value)", code)
        self.assertIn("function approve(address spender, uint256 value)", code)
        self.assertIn(
            "function transferFrom(address from, address to, uint256 value)", code
        )

    def test_generate_contract_different_decimals(self):
        name = "MyCoin"
        symbol = "MYC"
        initial_supply = 5000
        decimals = 8
        expected_adjusted_supply = initial_supply * (10**decimals)

        code = self.generator.generate_contract(name, symbol, initial_supply, decimals)

        self.assertIn(f"contract {name}", code)
        self.assertIn(f'string public symbol = "{symbol}";', code)
        self.assertIn(f"uint8 public decimals = {decimals};", code)
        self.assertIn(f"totalSupply = {expected_adjusted_supply};", code)
        self.assertIn(f"balanceOf[msg.sender] = {expected_adjusted_supply};", code)


if __name__ == "__main__":
    unittest.main()
