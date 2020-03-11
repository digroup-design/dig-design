import numpy as np
from sklearn.linear_model import LinearRegression
from pandas import DataFrame

def txt_to_dict(filename, headers=False)->(list, list):
    datatable = [r.strip().split('\t') for r in open(filename, 'r')]
    if headers:
        h = datatable.pop(0)
    else:
        h = ['y'] + [('x'+str(i)) for i in range(1, len(datatable[0]))]

    for i in range(0, len(datatable)):
        for j in range(0, len(datatable[i])):
            datatable[i][j] = float(datatable[i][j])

    datatable = np.transpose(datatable)
    dict = {}
    for i in range(0, len(h)):
        dict[h[i]] = datatable[i]
    return dict

inputs = txt_to_dict('SJ_Studios.txt', True)
df = DataFrame(inputs, columns=list(inputs.keys()))
x_list = [x for x in inputs.keys() if x != list(inputs.keys())[0]]

x = df[x_list]
y = df[list(inputs.keys())[0]]

reg = LinearRegression(fit_intercept=False).fit(x, y)
print(reg.intercept_)
for i in range(0, len(x_list)):
    print(x_list[i], reg.coef_[i])
