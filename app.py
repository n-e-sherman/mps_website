from flask import Flask, render_template, url_for, request, redirect, jsonify, send_file
from datetime import datetime
import json
import sys
import os
import subprocess
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
import matplotlib.colors as colors
from io import BytesIO
import base64

os.environ['FLASK_ENV'] = 'development'
app = Flask(__name__)

def rescale(zs, vmin = 0, vmax = 1):
    _zs = np.array(zs)
    zmin = np.min(_zs)
    zmax = np.max(_zs)
    res = ( (_zs - zmin) * (vmax - vmin) ) / (zmax - zmin) + vmin
    return res

def get_file_name(inputs, cwd):
	read_dir = 'code/.results/'
	if inputs['Correlation'] == "true":
		read_dir += 'correlationx/'
	if inputs['Chebyshev'] == "true":
		read_dir += 'chebyshevx/'
	read_dir += inputs['Model'] + '/'
	for file in os.listdir(cwd+read_dir):
		if not (file == '.gitkeep'):
			file_name = cwd + read_dir + file
	return file_name

def get_hash(inputs):
	shash = ""
	if inputs['Correlation'] == "true":
		shash='Correlation_'
	if inputs['Chebyshev'] == "true":
		shash='Chebyshev_'
	shash += inputs['thermal']+'_'+inputs['N']+'_'+inputs['Delta']+'_'+inputs['time']+'_'+inputs['MaxDim']+'.csv'
	return shash

def make_arguments(inputs):
	res = []
	for k, v in inputs.items():
		res.append('--' + k + '=' + str(v))
	return res

def make_plot(df):

	thermal = bool(df.thermal.unique())
	L = int(df.N.unique())
	c = str(int(L/2))
	xs = np.arange(1,L+1)
	cols = [str(x) for x in xs]
	Icols = ['I'+str(x) for x in xs]
	if (L%2) == 0:
		xs = np.arange(-int(L/2)+1,int(L/2)+1)
	else:
		xs = np.arange(-int(L/2)+1,int(L/2)+2)

	ts = np.array(df.t.unique())
	RZs = np.array(df[cols])
	AZs = np.sqrt(np.array(df[cols])**2 + np.array(df[Icols])**2)
	if thermal:
	    scale = 1
	    zs = rescale(abs(RZs),vmin = 2E-3, vmax = 1)
	else:
	    scale = 10
	    zs = rescale(AZs,vmin = 2E-3, vmax = 1)
	autoR = np.array(df[c])
	autoI = np.array(df['I'+c])
	autoA = np.sqrt(autoR**2 + autoI**2)

	# Make color plot
	fig = Figure()
	fig.set_size_inches(6, 4.5)
	ax = fig.subplots()
	levs = np.logspace(np.log10(scale*np.min(zs)), np.log10(np.max(zs)), 60)
	cax = ax.contourf(xs, ts, zs, levs, norm=colors.LogNorm(), extend='both')
	ticks = [levs[0],levs[-1]]
	labels = ['1E-5','1']
	cbar = fig.colorbar(cax, ticks=ticks)
	cbar.ax.set_yticklabels(labels)
	ax.set_xlabel('$x$',fontsize=14)
	ax.set_ylabel('$t$',fontsize=14)
	fig.tight_layout()
	buf = BytesIO()
	fig.savefig(buf, format="png")
	data_corr = base64.b64encode(buf.getbuffer()).decode("ascii")

	# Make auto-correlation plot
	fig = Figure()
	fig.set_size_inches(6, 4.5)
	ax = fig.subplots()
	ax.plot(ts,autoR,color='k',label='Real')
	ax.plot(ts,autoI,color='b',label='Imaginary',ls=':')
	ax.plot(ts,autoA,color='r',label='Magnitude',ls='--')
	ax.legend()
	ax.set_xlabel('$t$',fontsize=14)
	ax.set_ylabel('$|G(x=0,t)|$',fontsize=14)
	fig.tight_layout()
	buf = BytesIO()
	fig.savefig(buf, format="png")
	data_auto = base64.b64encode(buf.getbuffer()).decode("ascii")

	return f"data:image/png;base64,{data_corr}", f"data:image/png;base64,{data_auto}"


def run_code(inputs):
	_hash = get_hash(inputs)
	cwd = os.getcwd()+'/'
	_file = cwd+'code/.data/'+_hash
	if os.path.exists(_file):
		return pd.read_csv(_file)

	inputs['save'] = "false"
	inputs['write'] = "false"
	inputs['resDir'] = "code/"
	inputs['Silent'] = "true"
	inputs['SiteSet'] = "SpinHalf"
	inputs['Model'] = "XXZ"
	inputs['beta'] = 0
	inputs['Evolver'] = "Trotter"
	inputs['nSweeps'] = 5
	sweeps_maxdim = [np.max([1,int(1.0 / float(inputs['nSweeps']) * n * int(inputs['MaxDim']))]) for n in range(1, inputs['nSweeps'] + 1)]
	inputs['sweeps_maxdim'] = str(sweeps_maxdim).strip("[").strip("]").replace(" ", "")

	subprocess.run([cwd+"code/main"]+make_arguments(inputs))
	file_name = get_file_name(inputs, cwd)
	df = pd.read_csv(file_name)
	os.remove(file_name)
	df.to_csv(_file)
	return df

# setup initial page
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/correlation', methods=['GET','POST'])
def correlation():
	if request.method == 'POST':
		inputs = dict(request.form)
		inputs['Correlation'] = "true"
		inputs['Chebyshev'] = "false"
		url_cor, url_auto = make_plot(run_code(inputs))
		return render_template('correlation.html', url_cor=url_cor, url_auto=url_auto)
	else:
		return render_template('correlation.html', url_cor="static/plot/correlation.png", url_auto="static/plot/auto-correlation.png")


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port='8080') # For testing on times-login node
    app.run() #for deployment
