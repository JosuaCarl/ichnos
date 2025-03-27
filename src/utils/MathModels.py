def linear_model(a, b):
		# Linear model: y = ax + b
		return lambda x: a * x + b

def quadratic_model(a, b, c):
		# Quadratic model: y = ax^2 + bx + c
		return lambda x: a * x**2 + b * x + c

def cubic_model(a, b, c, d):
		# Cubic model: y = ax^3 + bx^2 + cx + d
		return lambda x: a * x**3 + b * x**2 + c * x + d