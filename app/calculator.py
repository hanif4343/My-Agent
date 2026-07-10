def add(num1: float, num2: float) -> float:
    """Return the sum of two numbers."""
    return num1 + num2

def subtract(num1: float, num2: float) -> float:
    """Return the difference of two numbers."""
    return num1 - num2

def multiply(num1: float, num2: float) -> float:
    """Return the product of two numbers."""
    return num1 * num2

def divide(num1: float, num2: float) -> float:
    """
    Return the quotient of two numbers.

    Raises:
        ValueError: If the second number is zero.
    """
    if num2 == 0:
        raise ValueError("Cannot divide by zero")
    return num1 / num2
