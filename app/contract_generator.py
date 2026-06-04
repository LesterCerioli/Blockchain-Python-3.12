class SmartContractGenerator:
    
    pass


class ERC20ContractGenerator(SmartContractGenerator):
    
    def generate_contract(self, name: str, symbol: str, initial_supply: int, decimals: int = 18) -> str:
        
        adjusted_initial_supply = initial_supply * (10**decimals)

        return f"""\

pragma solidity ^0.8.0;

contract {name} {{
    string public name = "{name}";
    string public symbol = "{symbol}";
    uint8 public decimals = {decimals};
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor() {{
        totalSupply = {adjusted_initial_supply};
        balanceOf[msg.sender] = {adjusted_initial_supply};
    }}

    function transfer(address to, uint256 value) public returns (bool success) {{
        require(balanceOf[msg.sender] >= value, "Insufficient balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }}

    function approve(address spender, uint256 value) public returns (bool success) {{
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }}

    function transferFrom(address from, address to, uint256 value) public returns (bool success) {{
        require(balanceOf[from] >= value, "Insufficient balance");
        require(allowance[from][msg.sender] >= value, "Allowance exceeded");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        emit Transfer(from, to, value);
        return true;
    }}
}}
"""
