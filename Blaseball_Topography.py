# -*- coding: utf-8 -*-
"""
Created on Thu Sep  2 19:18:13 2021

@author: MaxKo
"""

#code modified from https://www.geodose.com/2019/09/3d-terrain-modelling-in-python.html

import numpy as np
import plotly.offline as go_offline
import plotly.graph_objects as go
import scipy.ndimage
from blaseball_mike.chronicler import get_game_updates
from blaseball_mike.chronicler.v1 import time_season

eventIndex = 0
validSeason = False
validDay = False
validMatch = False

print('Select a Season from 1 to 24.')

while validSeason == False:
    mySeason = int(input())
    if 0 < mySeason and mySeason < 25:
        validSeason = True
    else:
        print('Season invalid.')

days = time_season(mySeason)[0]['days']

print('Select a day from 1 to ' + str(days) + '.')
while validDay == False:
    myDay = int(input())
    if 0 < myDay and myDay < days:
        validDay = True
    else:
        print('Date invalid.')
            
myGame = get_game_updates(season = mySeason, day = myDay)

matches = []

awayTeams = list(set(dic['data']['awayTeamName'] for dic in myGame))

i = 0
j = 0

while i < len(awayTeams):
    row = []
    row.append(awayTeams[i])
    row.append(next(dic['data']['homeTeamName'] for dic in myGame if dic['data']['awayTeamName'] == awayTeams[i]))
    matches.append(row)
    i += 1
    
print("Select a match.")

for match in matches:
    print(str(j + 1) + '. ' + matches[j][0] + ' vs ' + matches[j][1])
    j += 1

while validMatch == False:
    myMatch = int(input())
    if 0 < myMatch and myMatch < j + 1:
        validMatch = True
    else:
        print('Invalid entry.')
        
for gameEvent in myGame[::-1]:
    if gameEvent['data']['homeTeamName'] != matches[myMatch - 1][1]:
        myGame.remove(gameEvent)
        
#Turn blaseball data into 3d points

#READING AND PARSING THE DATA
x=[]
y=[]
z=[]

eventNum = 0

for gameEvent in myGame:
    play = gameEvent['data']['lastUpdate']
    if(play != ''):
        i = 0
        play.replace(' ', '')
        while i < len(play):
            x.append(300 / len(play) * i)
            y.append(eventNum)
            if play[i] == 'é':
                z.append(ord('e'))
            elif play[i] == 'ú':
                z.append(ord('u'))
            else:
                z.append(ord(play[i]))
            i += 1
    eventNum += 1    

#DISTANCE FUNCTION
def distance(x1,y1,x2,y2):
    d=np.sqrt((x1-x2)**2+(y1-y2)**2)
    return d

#CREATING IDW FUNCTION
def idw_npoint(xz,yz,n_point,p):
    r=10 #block radius iteration distance
    nf=0
    while nf<=n_point: #will stop when np reaching at least n_point
        x_block=[]
        y_block=[]
        z_block=[]
        r +=10 # add 10 unit each iteration
        xr_min=xz-r
        xr_max=xz+r
        yr_min=yz-r
        yr_max=yz+r
        i = 0
        for i in range(len(x)):
            # condition to test if a point is within the block
            if ((x[i]>=xr_min and x[i]<=xr_max) and (y[i]>=yr_min and y[i]<=yr_max)):
                x_block.append(x[i])
                y_block.append(y[i])
                z_block.append(z[i])
        nf=len(x_block) #calculate number of point in the block
    
    #calculate weight based on distance and p value
    w_list=[]
    for j in range(len(x_block)):
        d=distance(xz,yz,x_block[j],y_block[j])
        if d>0:
            w=1/(d**p)
            w_list.append(w)
            z0=0
        else:
            w_list.append(0) #if meet this condition, it means d<=0, weight is set to 0
    
    #check if there is 0 in weight list
    w_check=0 in w_list
    if w_check==True:
        idx=w_list.index(0) # find index for weight=0
        z_idw=z_block[idx] # set the value to the current sample value
    else:
        wt=np.transpose(w_list)
        z_idw=np.dot(z_block,wt)/sum(w_list) # idw calculation using dot product
    return z_idw

# POPULATE INTERPOLATION POINTS
n=100 #number of interpolation point for x and y axis
x_min=min(x)
x_max=max(x)
y_min=min(y)
y_max=max(y)
w=x_max-x_min #width
h=y_max-y_min #length
wn=w/n #x interval
hn=h/n #y interval

#list to store interpolation point and elevation
y_init=y_min
x_init=x_min
x_idw_list=[]
y_idw_list=[]
z_head=[]
for i in range(n):
    xz=x_init+wn*i
    yz=y_init+hn*i
    y_idw_list.append(yz)
    x_idw_list.append(xz)
    z_idw_list=[]
    for j in range(n):
        xz=x_init+wn*j
        z_idw=idw_npoint(xz,yz,5,1.5) #min. point=5, p=1.5
        z_idw_list.append(z_idw)
    z_head.append(z_idw_list)

#SMOOTHING
sigma = [1.5, 1.5]
z_head = scipy.ndimage.filters.gaussian_filter(z_head, sigma)
    
# CREATING 3D TERRAIN MODEL
# fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, mode='markers')])
fig=go.Figure()
fig.add_trace(go.Surface(z=z_head,x=x_idw_list,y=y_idw_list))
fig.update_layout(
    title = 'Season ' + str(mySeason) + ', Day ' + str(myDay) + ', ' + matches[myMatch - 1][0] + ' vs ' + matches[myMatch - 1][1],
    scene=dict(aspectratio=dict(x=2, y=2, z=0.5),xaxis = dict(range=[x_min,x_max],),yaxis = dict(range=[y_min,y_max])))
go_offline.plot(fig,filename= 'S' + str(mySeason) + 'D' + str(myDay) + 'M' + str(myMatch) + '.html',validate=True, auto_open=True)