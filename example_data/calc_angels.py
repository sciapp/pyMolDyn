from math import acos

import numpy as np

# 128
#a = np.array([14.67248,8.47112,0.0])
#b = np.array([22.00872,-12.70668,0.0])
#c = np.array([7.3362,12.70668,10.37496])

# 168
a = np.array([14.67248,8.47112,0.0])
b = np.array([14.67248,-8.47112,0.0])
c = np.array([0.0,0.0,30.0])

# 196
# a = np.array([22.00872,12.70668,0.0])
# b = np.array([22.00872,-12.70668,0.0])
# c = np.array([7.3362,12.70668,10.37496])

an = np.linalg.norm(a)
bn = np.linalg.norm(b)
cn = np.linalg.norm(c)

alpha = acos((a.dot(c))/(an*cn))
beta  = acos((b.dot(c))/(bn*cn))
gamma = acos((a.dot(b))/(an*bn))

print an, bn, cn
print alpha, beta, gamma
