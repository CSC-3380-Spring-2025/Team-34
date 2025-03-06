import sympy as sp

x = sp.Symbol('x')
expr = x**2 + 3*x + 2
derivative = sp.diff(expr, x)

print(f"Expression: {expr}")
print(f"Derivative: {derivative}")
