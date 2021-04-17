from flask import Flask, request, render_template, redirect, send_from_directory
from RunSlope64v2 import runSlope2, sfOut, wiper, zipResults
from pathlib import Path  

app = Flask(__name__)
 
staticPath = Path.cwd().joinpath('static')

def toReal(strVal ):
    return round(float(strVal),2)

def toStr(flVal):
    return "{:.2f}".format(flVal)


@app.route('/', methods = ['GET','POST'])
def run():
   if request.method == 'POST':
       soilPrs = []
       params =  request.form
       hd = {'damName': params['damName']}
       geo = {'w1': toReal(params['w1']), 's1' : toReal(params['s1']), 'w2' :toReal(params['w2']), 's2' : toReal(params['s2']), 'w3' : toReal(params['w3']), 'h1': toReal(params['h1']), 'h2' : toReal(params['h2']) }
       mesh = {'nx1': int(params['nx1']), 'nx2': int(params['nx2']), 'nx3': int(params['nx3']), 'ny1': int(params['ny1']), 'ny2': int(params['ny2']) }
       soilPrs.append({'phi' : toReal(params['phi1']), 'c': toReal(params['c1']), 'uW' : toReal(params['uW1']), 'E' : int(params['E1']) , 'v' : toReal(params ['v1']) })
       soilPrs.append({'phi' : toReal(params['phi2']), 'c': toReal(params['c2']), 'uW' : toReal(params['uW2']), 'E' : int(params['E2']) , 'v' : toReal(params ['v2']) }) 
       wtr = [toReal(params['hw']), params['wAnalysis']]
       print(wtr)
       runSlope2(hd,geo,mesh,soilPrs,wtr)       
       return redirect('/results')


   else :
    try:
        wiper()
    except: pass        
    return render_template('Run.html')

@app.route('/results', methods = ['GET','POST'])
def results():
    if request.method == 'POST':
        zipResults(['in.dat','in.dis','in.msh','in.res','in.vec'])
        return send_from_directory(Path.cwd(),'results.zip', as_attachment=True)
    else:
        return render_template('Results.html' , SF = sfOut())