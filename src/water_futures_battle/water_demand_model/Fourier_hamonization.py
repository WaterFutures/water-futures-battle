import numpy as np
from scipy.io import loadmat

data = loadmat("data.mat")["data"]
esp = loadmat("esp.mat")["esp"]

t_horizon = 25
Narmoniche = 3

CH_obs = data/np.mean(data)
CH_mat = CH_obs.reshape((24, 365))
mean_die = np.mean(CH_mat, axis=0)
CH_mat_adim = np.divide(CH_mat, np.matlib.repmat(mean_die, 24, 1))

y = np.copy(mean_die)
x = list(range(1, 365 + 1))

Ndati = len(y)
tau = np.array(list(range(1, Ndati + 1)))
azero = np.mean(y, axis=0)
a = []
b = []
for k in range(Narmoniche):
    a.append((2/Ndati)*np.sum(np.multiply(y, np.cos(k*(2*np.pi*tau)/Ndati))))
    b.append((2/Ndati)*np.sum(np.multiply(y, np.sin(k*(2*np.pi*tau)/Ndati))))

a = np.array(a)
b = np.array(b)

var_min = 0.5
var_max = 1.5
a_orig = np.copy(a)
b_orig = np.copy(b)
yFourier = np.zeros((Narmoniche+1, x[-1]))
yFourier[0, :] = np.ones((1, Ndati))*azero
qmedia_dieFour = np.zeros((t_horizon, x[-1]))


Ny = t_horizon
for yy in range(Ny):
    a = np.multiply(a_orig, var_min+(var_max-var_min)*np.matlib.rand(Narmoniche))
    b = np.multiply(b_orig, var_min+(var_max-var_min)*np.matlib.rand(Narmoniche))

    for k in range(Narmoniche):
        yFourier[k+1, :] = yFourier[k, :] + a[:, k]*np.cos(tau*(2*np.pi*k)/Ndati) + b[:, k]*np.sin(tau*(2*np.pi*k)/Ndati)

    qmedia_dieFour[yy, :] = yFourier[Narmoniche, :]

for yy in range(Ny):
    qmedia_dieFour[yy, :] = np.power(qmedia_dieFour[yy, :], esp[yy])


varDie_min = 0.95
varDie_max = 1.05

qmedia_die = np.multiply(qmedia_dieFour, varDie_min+(varDie_max-varDie_min)*np.matlib.rand(Ny, 365))

varh_min = 0.95
varh_max = 1.05
CH_series_gen = np.zeros((8760, t_horizon))

for yy in range(Ny):
    CH_mat_adim_year = np.multiply(CH_mat_adim, (varh_min+(varh_max-varh_min)*np.matlib.rand(24, 365)))
    CH_mat_gen = np.multiply(np.matlib.repmat(qmedia_die[yy, :], 24, 1), CH_mat_adim_year)
    CH_series_gen[:, yy] = CH_mat_gen.reshape((1, 24*365))

FINAL_data = CH_series_gen  # coeff. (-): 8760 hours x n. years (time_horizon)
print(FINAL_data.shape)
