import numpy as np
from scipy import stats
import statsmodels.api as sm

def txt_to_array(filename)->(list, list):
    datatable = [r.strip().split('\t') for r in open(filename, 'r')]
    for i in range(0, len(datatable)):
        for j in range(0, len(datatable[i])):
            datatable[i][j] = float(datatable[i][j])

    np.transpose(datatable)
    #y = [r.pop(0) for r in datatable]
    y = datatable.pop(0)
    x = datatable
    return x, y

inputs = txt_to_array('SJ_Studios.txt')
x = np.transpose(inputs[0])
y = inputs[1]
print(x, y)
print(stats.mstats.linregress(x, y))



def func_rent_per_sf(coeff: list):
    pass