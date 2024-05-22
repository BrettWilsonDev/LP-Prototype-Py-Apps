import sympy as sp

d = sp.symbols('d')

# d is delta

                                            # change this to inverse of bv
matbNeg1 = sp.Matrix([[1, 2, -8],
                     [0, 2, -4],
                     [0, -0.5, 1.5]])


matCbv = sp.Matrix([[0], [20], [60]]) # change this to the cbv of z example (60+d)

zTop = (30) # the z that is being delta example (30+d)
matA = sp.Matrix([[6], [2], [1.5]]) # change this to the col of the z

matB = sp.Matrix([[48+d], [20], [8]]) # change this to the rhs col example (48+d)

#  ============================================= dont touch =============================================

matCbv_transpose = matCbv.T

matCbvNeg1 = matCbv_transpose * matbNeg1
print("\nq or cbvB-1")
sp.pprint(matCbvNeg1)

matC = matCbvNeg1 * matA

result_value = matC[0] - (zTop)

print("\nz row value C*")
print(result_value)
print()

matRhs = matCbvNeg1 * matB

result_valueRhs = matRhs[0]

print("\nrhs col b*")
matBStar = matbNeg1 * matB

sp.pprint(matBStar)

print("\noptimal rhs*")
print(result_valueRhs)
print()
