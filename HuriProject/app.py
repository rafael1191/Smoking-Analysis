from flask import Flask, render_template, url_for, request, redirect
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import requests
import pandas as pd
import json
import plotly
import plotly.express as px
from bs4 import BeautifulSoup
import requests
import re
import numpy as np
import os

# Create Home Page Route
app = Flask(__name__)

def TurnPlotToImage(plotParam):
    #creates a buffer, kinda like not saved file which we can use to save the image for now
    buffer = BytesIO()

    #Creating a new figure
    a = plotParam.figure

    #Save the figure in the buffer as png
    a.savefig(buffer, format='png')

    #Point to the beggining of the file
    buffer.seek(0)

    #Encode the png so we can show it in the html web
    plot_image = base64.b64encode(buffer.getvalue()).decode()

    return plot_image


def GetNews():
    
    #Get the BBC news page about smoking - html code
    url = 'https://www.bbc.com/news/topics/c50znx8v8q8t'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html')
    Texts=[]
    Urls2=[]

    #Find all the news text and url
    selectedF = soup.findAll('a',{'class' : 'ssrcss-1mrs5ns-PromoLink exn3ah91'}) 
    Urls = re.findall('href=\"/(?:[-\w.]|(?:%[\da-fA-F]{2}))+/(?:[-\w.]|(?:%[\da-fA-F]{2}))+\"', str(selectedF)) 

    for div in soup.findAll('p',{'class' : 'ssrcss-17zglt8-PromoHeadline exn3ah96'}):
        Texts.append(div.get_text())
    for j in range(0,len(Urls)):
        j2=Urls[j].replace('href=\"','https://www.bbc.com')
        Urls2.append(j2)
        
        
    #take only first 5
    Urls2=Urls2[0:5]
    Texts=Texts[0:5]
    
    #combine the 2 1d arrays into one 2d array
    news=np.vstack((Texts,Urls2)).T
    
    newselm=""
    #Make them an html code links
    for i in news:
        try:
            newselm=newselm + ' <a href="'+i[1]+'">'+i[0]+'</a></br>'
        except: pass
    return newselm

def loaddf():
    
    #Load the csv file from what path the app file is running from
    df = pd.read_csv(os.getcwd()+r'\survey lung cancer.csv')
    
    #Beautify the data
    df.loc[df["AGE"] < 20 , "AGE2"] = "0-20"
    df.loc[(df["AGE"] > 20) & (df["AGE"] < 40), "AGE2"] = "20-40"
    df.loc[(df["AGE"] > 40) & (df["AGE"] < 60), "AGE2"] = "40-60"
    df.loc[(df["AGE"] > 60) & (df["AGE"] < 80), "AGE2"] = "60-80"
    df = df[['GENDER','AGE2','SMOKING','YELLOW_FINGERS','PEER_PRESSURE','COUGHING','ALCOHOL CONSUMING','LUNG_CANCER']].copy()
    df.loc[df["LUNG_CANCER"] == 1, "LUNG_CANCER"] = "No Cancer"
    df.loc[df["LUNG_CANCER"] == 2, "LUNG_CANCER"] = "Cancer"
    df.loc[df["YELLOW_FINGERS"] == 1, "YELLOW_FINGERS"] = "No YELLOW FINGERS"
    df.loc[df["YELLOW_FINGERS"] == 2, "YELLOW_FINGERS"] = "YELLOW FINGERS"
    df.loc[df["GENDER"] == 0, "GENDER"] = "Female"
    df.loc[df["GENDER"] == 1, "GENDER"] = "Male"
    df.loc[df["SMOKING"] == 1, "SMOKING"] = "No SMOKING"
    df.loc[df["SMOKING"] == 2, "SMOKING"] = "SMOKING"
    df.loc[df["PEER_PRESSURE"] == 1, "PEER_PRESSURE"] = "No PEER PRESSURE"
    df.loc[df["PEER_PRESSURE"] == 2, "PEER_PRESSURE"] = "PEER PRESSURE"
    df.loc[df["COUGHING"] == 1, "COUGHING"] = "No COUGHING"
    df.loc[df["COUGHING"] == 2, "COUGHING"] = "COUGHING"
    df.loc[df["ALCOHOL CONSUMING"] == 1, "ALCOHOL CONSUMING"] = "No ALCOHOL CONSUMING"
    df.loc[df["ALCOHOL CONSUMING"] == 2, "ALCOHOL CONSUMING"] = "ALCOHOL CONSUMING"
    df = df[df['SMOKING'] == "SMOKING"].copy()
    
    #Assign id to each row
    df = df.assign(id=range(len(df)))
    
    return df
    
#First page navigation
@app.route('/')
def routs():
    return render_template('bar.html')

#News page
@app.route('/news',methods=['POST', 'GET'])
def news():
    
    #Load news
    newselm=GetNews()
    
    #Render the news page
    return render_template('bar.html',newselm=newselm)

#Home page (csv table)
@app.route('/home',methods=['POST', 'GET'])
def home():
    #Token to show only the csv
    home="a"
    #htmlcsvdata=df.to_html()
    
    #Load the DataFrame and beautify it
    df = loaddf()
    a= df.head(10).to_html()
    
    #Set up the page number to toggle between pages
    try: PageNum
    except NameError:
        PageNum = 0
        
    #Render Home page with all the params
    return render_template('bar.html', home=home, table=a,PageNum=PageNum)

#When right click to advance to the next page
@app.route('/righttable',methods=['POST', 'GET'])
def rightclick():
    home="a"
    df = loaddf()
    
    #Get the num page
    PageNum = int(request.form['PageNum'])
    
    if(PageNum==len(df)/10):
        pass
    
    else:
        PageNum2=PageNum+1
        a = df[PageNum2*10:PageNum2*10+10].to_html()
        
        #Render the next page
        #Take a note that each time I render the next page i am saving the num page in a hidden textbox
        return render_template('bar.html', home=home, table=a,PageNum=PageNum2)

#When right click to advance to the previous page
@app.route('/lefttable',methods=['POST', 'GET'])
def leftclick():
    home="a"
    
    #Get the num page
    PageNum = int(request.form['PageNum'])
    
    if(PageNum==0):
        return redirect('/home')
    
    else:
        df = loaddf()
        PageNum2=PageNum-1
        a = df[PageNum2*10:PageNum2*10+10].to_html()
        
        #Render the next page
        #Take a note that each time I render the next page i am saving the num page in a hidden textbox
        return render_template('bar.html', home=home, table=a,PageNum=PageNum2)

#On click search specific ID
@app.route('/searchontable',methods=['POST'])
def search():
    home="a"
    
    #Get the ID
    whatid = request.form['whatid']
    df = loaddf()
    
    #Search the ID
    a = df[df['id'] == int(whatid)].to_html()
    
    #Render the wanted table
    return render_template('bar.html', home=home, table=a)


@app.route('/analysis',methods=['POST', 'GET'])
def analysis():
    df = loaddf()
    df_have = df[df['LUNG_CANCER'] == "Cancer"]
    
    #Make the bar visualization
    pivot_table= pd.pivot_table(df_have[["AGE2","GENDER", "LUNG_CANCER"]].groupby(['AGE2','GENDER']).count(),index='AGE2', columns='GENDER', values='LUNG_CANCER').plot(kind='bar')

    #turn the visualization to img
    plot_image = TurnPlotToImage(pivot_table)
    
    #Make the wanted statistic table to html code
    plot_table = df_have[["YELLOW_FINGERS","GENDER","LUNG_CANCER"]].groupby(['YELLOW_FINGERS','GENDER']).count().to_html()

    #Render all
    return render_template('bar.html', plot_image=plot_image,yellowfingertable=plot_table)

if __name__ == '__main__':
    app.run()