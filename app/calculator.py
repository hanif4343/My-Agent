class Calculator:
    def add(self, num1: float, num2: float) -> float:
        """Return the sum of two numbers."""
        return num1 + num2

    def subtract(self, num1: float, num2: float) -> float:
        """Return the difference of two numbers."""
        return num1 - num2

    def multiply(self, num1: float, num2: float) -> float:
        """Return the product of two numbers."""
        return num1 * num2

    def divide(self, num1: float, num2: float) -> float:
        """Return the quotient of two numbers."""
        if num2 == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return num1 / num2


def main():
    calculator = Calculator()
    print(calculator.add(10, 5))  # Output: 15
    print(calculator.subtract(10, 5))  # Output: 5
    print(calculator.multiply(10, 5))  # Output: 50
    print(calculator.divide(10, 2))  # Output: 5.0


if __name__ == "__main__":
    main()
