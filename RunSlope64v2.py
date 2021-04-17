from datetime import datetime

import subprocess
from pathlib import Path 
import shutil 
import matplotlib.pyplot as plt
import os 
from zipfile import ZipFile 

appPath = Path.cwd()
tpPath = appPath.joinpath('templates')
staticPath = appPath.joinpath('static')

nl2 = '\n'+'\n'

#function for defining the water table coordinates
#parameters:
# fg = flag that takes two values, ResW = Water in the reservoir,  RpD = Rapid Drawdown
# geom = geometry of the dam 
# hw = watertable on the reservior or just before the drawdown, depending on the case 

def wtSpecs(fg,geom,hw) :

   hwC = []
   if fg == 'ResW' : 
        hwC.append([0,hw]) 
        hwC.append([geom['w1']+hw/geom['h1']*geom['s1'],hw])
        hwC.append([geom['w1']+geom['s1']+geom['w2']+geom['s2'],0])
        hwC.append([geom['w1']+geom['s1']+geom['w2']+geom['s2']+geom['w3'],0])
   
   if fg == 'RpD':
        hwC.append([0,0])
        hwC.append([geom['w1'],0]) 
        hwC.append([geom['w1']+hw/geom['h1']*geom['s1'],hw])
        hwC.append([geom['w1']+geom['s1']+geom['w2']+geom['s2'],0])
        hwC.append([geom['w1']+geom['s1']+geom['w2']+geom['s2']+geom['w3'],0])

   return hwC
   
# function for writing the inputfile
# parameters
# heading: dam name
# geom : dictionary containing the dam geometrical properties
# mesh : mesh defining the discretization pattern 
# geoPrs : Dictionary containing the mechanical properties of each type of soil/tailings
# water : list describing the watertable : [water table height, type of analysis being made ResW = Water in the reservoir,  RpD = Rapid Drawdown )]
 
def runFile(heading, geom, mesh, geoPrs, water):
    
    output = '"' + heading['damName'] + ", " + datetime.now().strftime('%Y-%m-%d , %H:%M:%S') + ' "' + nl2
    nGroups = len(geoPrs)

    # Geometry Data
    output += 'w1:' + '\n' + "{:.2f}".format(geom['w1']) + nl2 + 's1:' + '\n' + "{:.2f}".format(geom['s1']) + nl2 + 'w2:' + '\n' + "{:.2f}".format(geom['w2']) + nl2   
    output += 's2:' + '\n' + "{:.2f}".format(geom['s2']) + nl2 + 'w3' + '\n' + "{:.2f}".format(geom['w3']) + nl2 
    output +=  'h1:' + '\n' + "{:.2f}".format(geom['h1'])+ nl2 + 'h2:' + '\n' + "{:.2f}".format(geom['h2']) + nl2

    #Mesh Characteristics
    output += 'nx1:' + '\n' + str(mesh['nx1']) + nl2 + 'nx2:' + '\n' + str(mesh['nx2']) + nl2 + 'nx3:' + '\n' + str(mesh['nx3']) + nl2
    output += 'ny1:' + '\n' + str(mesh['ny1']) + nl2 + 'ny2:' + '\n' + str(mesh['ny2']) + nl2      

    #Soil Mechanical properties
    output += 'Property groups:' + '\n' + str(nGroups) + nl2    
    output += "material properties:" + '\n'
    for x in geoPrs :
        output += "{:.2f}".format(x['phi']) + ' ' + "{:.2f}".format(x['c']) + ' 0.0 ' + "{:.2f}".format(x['uW']) + ' ' + str(x['E']) + ' ' + "{:.2f}".format(x['v']) + '\n'
    output += '\n'

    #Propery Asigmements for each element:
    output += 'property Asignements to each element:'
    if nGroups == 1 : 
        output += nl2
    if nGroups > 1:
        output += '\n'
        output +=  geoAsnProps(mesh['nx1'],mesh['nx2'],mesh['nx3'],mesh['ny1'],mesh['ny2']) 
        output += '\n'
           
    #Pseudo-Static Analysis
    output += 'Kh:' + '\n' + '0.0' + nl2

    #Watertable

    output += 'WaterTable Coordinates x,y :' + '\n' 
    hwC = wtSpecs(water[1], geom, water[0])
    output += str(len(hwC)) + '\n'

    for x in hwC :
        output += "{:.2f}".format(x[0]) + " " + "{:.2f}".format(x[1]) + '\n'

    output += '\n'+'unit weight of water:' + '\n' + str(10) + nl2
    output += 'iteration ceiling:' + '\n' + str(2000) + nl2
    output += 'FS accurracy:' + '\n' + str(0.05) 
    return output

def geoLnProps(props):
    row = ' '
    for x in props:
        for i in range(0, x[1]):
            row += str(x[0]) + ' '
    row += '\n'
    return row       

def geoAsnProps (nx1,nx2,nx3,ny1,ny2):
    out = ''
    for i in range(0, ny1) :
        out += geoLnProps([[' ',nx1],[1,nx2],[' ', nx3]])
    for i in range(0,ny2) :    
        out += geoLnProps([[2,nx1+nx2+nx3]])
    return out 

def readDisp(fname):
    f = open(fname)
    rfile = f.readlines()
    rfile[0:34] = []
    bx = []
    by = []
    px = []
    py = []
    dx = []
    dy = []
 

    for x in rfile:
        a = x.split()
        if len(a) == 3:  
           bx.append(float(a[0])) 
           by.append(float(a[1]))
        if len(a) == 5:
           px.append(float(a[0]))
           py.append(float(a[1]))
           dx.append(round(float(a[2])-float(a[0]),2))
           dy.append(round(float(a[3])-float(a[1]),2))

   
    return [[px,py,dx,dy],[bx,by]] 
 
def runSlope2 (hd,geo,mesh,geoPrs,wtr): 
    
    # function for running Slope2 and generating all output fields. 
    # input parameters: 
    # hd = heading, geo = geometrical outline, mesh = mesh characteristics, geoPrs geomechanical parameters, 
    # wtrs = watertable analysis and height. 
    # hd = {'damName': 'Damn Name'}
    #geo = {'w1': see figure1, 's1' : see figure1, 'w2' : see figure1, 's2' : see figure1, 'w3' : see figure1, 'h1': see figure1, 'h2' : see figure1 }
    #mesh ={'nx1': see figure2, 'nx2': see figure2, 'nx3': see figure 2, 'ny1': see figure 2, 'ny2': see figure 2 }
    #geoPrs = [{'phi' : effective internal frictiona angle, 'c': effective cohesion, 'uW': unitary weigth , 'E' : Young's Modulus, 'v' : poission ratio}
    #wtr = ['RPD' for Rapid Drawdown or ResW for water in the reservoir, last water level in the reservoir]
    
    inFile = runFile(hd,geo,mesh,geoPrs,wtr)
    
    with open ('in.dat' , 'w') as f:
        f.write(inFile)
    
    subprocess.call(['slope2.exe','in'])
    fl = readDisp('in.vec')
    plt.quiver(fl[0][0],fl[0][1],fl[0][2],fl[0][3])
    plt.scatter(fl[1][0],fl[1][1])
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.savefig('VectorField.png')
    shutil.move('VectorField.png',staticPath.joinpath('VectorField.png') )
    #plt.show()

def wiper(): 
    os.remove('in.dat')
    os.remove('in.dis')
    os.remove('in.msh')
    os.remove('in.res')
    os.remove('in.vec')
    os.remove(staticPath.joinpath('VectorField.png'))

def sfOut():
    with open ('in.res','r') as f:
        wholeF = f.readlines()
    wholeF = wholeF[-1].split()
    return wholeF[-1]   

def zipResults (list): 
    zipR = ZipFile('results.zip','w')
    for x in list:
        zipR.write(x)
    zipR.close()    
        
#hd = {'damName': 'Macacos'}
#geo = {'w1': 33.5, 's1' : 66.2, 'w2' : 7.3, 's2' : 50.9, 'w3' : 33.5, 'h1': 21.3, 'h2' : 14.6 }
#mesh ={'nx1': 5, 'nx2': 10, 'nx3': 5, 'ny1': 10, 'ny2': 5 }
#geoPrs = [{'phi' : 30, 'c': 10, 'uW': 18.2 , 'E' : 1.e5, 'v' : 0.3},{'phi' : 20, 'c': 5, 'uW': 18.2 , 'E' : 1.e5, 'v' : 0.3} ]
#wtr = ['ResW',17.1]
#runSlope2(hd,geo,mesh,geoPrs,wtr)

#wiper()
#print(sfOut())
#outFiles = ['in.dat','in.dis','in.msh','in.res','in.vec']
#zipResults(outFiles)
