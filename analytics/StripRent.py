import numpy as np
from sklearn.linear_model import LinearRegression
from pandas import DataFrame

def txt_to_dict(filename)->(list, list):
    dict = {}
    datatable = [r.strip().split('\t') for r in open(filename, 'r')]
    for i in range(0, len(datatable)):
        for j in range(0, len(datatable[i])):
            datatable[i][j] = float(datatable[i][j])

    datatable = np.transpose(datatable)
    dict['y'] = datatable[0]
    for i in range(1, len(datatable)):
        dict['x'+str(i)] = datatable[i]
    return dict

inputs = txt_to_dict('SJ_Studios.txt')
df = DataFrame(inputs, columns=list(inputs.keys()))
x_list = [x for x in inputs.keys() if x is not 'y']

x = df[x_list]
y = df['y']

reg = LinearRegression().fit(x, y)
print(reg.intercept_)
print(reg.coef_)
