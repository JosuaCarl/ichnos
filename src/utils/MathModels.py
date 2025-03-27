"""
coefficients is a list of coefficients for the polynomial model
The model will be of the form:
y = a_n * x^n + a_(n-1) * x^(n-1) + ... + a_1 * x + a_0
where n is the degree of the polynomial and a_i are the coefficients
"""
def polynomial_model(coefficients):
		# Polynomial model: y = a_n * x^n + a_(n-1) * x^(n-1) + ... + a_1 * x + a_0
		def model(x):
			result = 0
			for i, coeff in enumerate(coefficients):
				result += coeff * (x ** (len(coefficients) - 1 - i))
			return result
		return model
	
linear_model = lambda a, b: polynomial_model([a, b])
quadratic_model = lambda a, b, c: polynomial_model([a, b, c])
cubic_model = lambda a, b, c, d: polynomial_model([a, b, c, d])
