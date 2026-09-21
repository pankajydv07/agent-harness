#!/usr/bin/env python3
"""
Simple calculator module.
Provides basic arithmetic operations.
"""

def add(a, b):
    """Return the sum of a and b."""
    return a + b

def subtract(a, b):
    """Return the difference of a and b."""
    return a - b

def multiply(a, b):
    """Return the product of a and b."""
    return a * b

def divide(a, b):
    """Return the quotient of a and b.
    
    Raises:
        ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b



if __name__ == "__main__":
    # Simple command-line interface for testing
    import sys
    if len(sys.argv) != 4:
        print("Usage: python calculator.py <operation> <num1> <num2>")
        print("Operations: add, subtract, multiply, divide, power, modulus")
        sys.exit(1)
    
    op = sys.argv[1]
    try:
        num1 = float(sys.argv[2])
        num2 = float(sys.argv[3])
    except ValueError:
        print("Error: Numbers must be valid numeric values.")
        sys.exit(1)
    
    operations = {
        'add': add,
        'subtract': subtract,
        'multiply': multiply,
        'divide': divide,
        
    }
    
    if op not in operations:
        print(f"Error: Unsupported operation '{op}'.")
        print(f"Available operations: {', '.join(operations.keys())}")
        sys.exit(1)
    
    try:
        result = operations[op](num1, num2)
        print(f"Result: {result}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)