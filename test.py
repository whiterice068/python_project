import pandas as pd
import numpy as np

# a = pd.Series([1,2,3,4,0,0,7,8])
# b = pd.Series([3,4,2,8,0,0,6,0])

# error = a/b


# print(type(error.iloc[5]))
data = pd.Series([10, 11, 12, 13, 14, 15, 16, 17])
print(data.ewm(span=2, adjust=False).mean())