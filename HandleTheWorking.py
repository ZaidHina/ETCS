#!/usr/bin/env python

import re
from typing import final 
import requests
import sys
import time #for sleep
from math import radians, cos, sin, asin, sqrt 
import mysql.connector
from requests.api import delete #to access mysql using python
import paho.mqtt.client as paho
from paho.mqtt import client as mqtt_client

import random #for mqtt
q=0


#Function opentxt used to open *.txt file (remove new line from the list) --> opentxt(filename.txt,'characters to remove')
def opentxt(FileName,chars):
        file=[]
        with open(FileName, "rb") as fp:
                for i in fp.readlines():
                    tmp=str(i).split(" ")
                    file.append(tmp)
        
        for i in range(len(file)):
            for j in range(len(file[i])):  #j to move in same row  
                str1=file[i][j]
                if j==0:
                    file[i][j] =  file[i][0][:0] + file[i][0][2:]
                            #in len(file[i][j]):
                for character in "\\n'":
                    file[i][j] = file[i][j].replace(character, "")          
        return file
sss=opentxt("asktrfs.txt","\\n'")   

class main: #main used regular expression to get the data for wanted id and find if new data arrived
    trf_INFOS = []
    reqid_INFOS=[]
    
    def __init__(self,trf,url,cli):
        self.trf=trf
        self.url=url
        self.cli=cli
        self.reqid_INFOS=[]
        self.ids=""
        self.trf_INFOS=[]

        self.trf_INFOS=opentxt(self.trf,"\\n'")#have all blocks info
        

    def get_REGEX(self):
        r = requests.get(self.url)
        self.ids = re.findall('<tr>\s+<td>(\d+)<br></td>\s+<td>(\d+.\d+)<br></td>\s+<td>(\d+.\d+)<br></td>\s+<td>(\w+)<br></td>\s+<td>(\d+-\d+-\d+\s+\d+:\d+:\d+)<',r.text)
        for p in range(len(self.ids)):
            if(self.cli == self.ids[p][0]):
                self.reqid_INFOS.append(self.ids[p])
                break 
        if len(self.reqid_INFOS)==0:
            print("Waiting 4.5 second to get next Location UPDATE...")
            time.sleep(4.5)
            return "empty"
        else:
            for i in range(len(self.ids)):
                temp = self.ids[i][0]
                if temp ==  self.reqid_INFOS[0][0]:
                    self.reqid_INFOS.append(self.ids[i])
            self.reqid_INFOS.pop(0)
            return "work"    
   
    def new_get_REGEX(self):
                newr = requests.get(self.url)
                newids = re.findall('<tr>\s+<td>(\d+)<br></td>\s+<td>(\d+.\d+)<br></td>\s+<td>(\d+.\d+)<br></td>\s+<td>(\w+)<br></td>\s+<td>(\d+-\d+-\d+\s+\d+:\d+:\d+)<',newr.text)
                if len(newids) != len(self.ids) :
                        return newids
                return "No data"

			


class work: #work used to find traffics in range of 5 KM --> if so,  
            #                                                      find if any of them less than 1 KM --> if so,
            #                                                            Give three attempts to get all prospect traffics which can be less than 1 KM
            # also, used for move data to Backup database 
    reqid_INFO=[]
    trf_INFOS=[]
    def __init__(self,reqid_INFO,ids,trfinfo):
        self.reqid_INFO=reqid_INFO
        self.ids=ids
        self.trf_INFOS=trfinfo
        self.tmpDistnace=[]

        self.Distance_Flag=1
        self.mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="toor",
        database="ETCSLocations"
        )

        self.mycursor = self.mydb.cursor()
    
    def findDistance(self):
        for i in range(len(self.reqid_INFO)):
            for x in range(len(self.trf_INFOS)):
                    dlat=radians(float(self.reqid_INFO[i][1]))-radians(float(self.trf_INFOS[x][1]))
                    dlon = radians(float(self.reqid_INFO[i][2]))-radians(float(self.trf_INFOS[x][2]))
                    V1=2 * asin(sqrt(sin(dlat / 2)**2 + cos(float(self.trf_INFOS[x][1])) * cos(float(self.reqid_INFO[i][1])) * sin(dlon / 2)**2))
                    d = 6371 * V1
                    if d < 5 :
                        self.tmpDistnace.append(d)
                        self.tmpDistnace.append(self.trf_INFOS[x][0])
                        self.tmpDistnace.append(self.reqid_INFO[i][3])  
                    if d < 1 :
                        self.Distance_Flag=0
        if self.Distance_Flag == 1:   
            counter=3
            for i in range(len(self.tmpDistnace)):
                if i ==0:
                    print("\nScanning for light traffics in range 5 KM...")
                    print("the  distance between point and "+str(self.tmpDistnace[i+1])+" traffic is "+str(self.tmpDistnace[i])+" KM \n")
                if i == counter:
                    print("the  distance between point and "+str(self.tmpDistnace[i+1])+" traffic is "+str(self.tmpDistnace[i])+" KM \n")
                    counter+=3

            tmp=work(None,None,None)
            return 1  
        else:
            return 0

   
                
    
    def backupDB(self):
                sql = "DELETE FROM GPS WHERE ID = "+sys.argv[1]+""

                self.mycursor.execute(sql)

                self.mydb.commit()


class worklessthan1Km: #wordlessthan1Km used to print the 3 attemps including the traffics , if last attemps call callTRF(class Ask_For_Trf)
    def __init__(self,req_IDS,trf_INFOS,meters,tmpDistance):
        self.req_IDS=req_IDS
        self.trf_INFOS=trf_INFOS
        self.meters=meters
        self.tmpDistance=tmpDistance
 

    def lessthan1Km(self,oldlen):
        tmpDis=self.tmpDistance
        tempname=[]
        print("Scanning "+str(self.meters)+"00(m):")
        counter=0
        for i in range(len(tmpDis)):
                if i == counter:
                    print("the  distance between point and "+str(tmpDis[i+1])+" traffic is "+str(tmpDis[i])+" KM \n")
                    counter+=3
                
                    if self.meters == 3:   
                        if tmpDis[i] < 1:
                            tempname.append(tmpDis[i+1])
                            tempname.append(tmpDis[i+2])
                        
                            
        if self.meters == 3: #end of 3 attemps so call function callTRF from class Ask_For_Trf
            tmp=Ask_For_Trf(tempname,"asktrfs.txt",self.req_IDS)
            tmp.callTRF()
                   
class Ask_For_Trf: #Ask_For_Trf used to get the traffics which we want to open then send to wanted traffics to turn green via Mqtt broker 
    foc_info=[]
   
    def __init__(self,foc_names,SubInfo,ETCS_lastinfo):
        self.foc_names=foc_names #has name+prio
        self.Subs=SubInfo
        self.SubInfo=[] 
        self.SubInfo=opentxt(self.Subs,"\n")
        self.ETCS_lastinfo=ETCS_lastinfo        
    def callTRF(self):
        ids_of_foc_trfs=[]
        req_info=[]
        req_id=[]
        for i in range(len(self.SubInfo)):
            for j in range(len(self.foc_names)):
                if j % 2 == 0:
                    if self.SubInfo[i][0] == self.foc_names[j]:
                        ids_of_foc_trfs.append(i)
                        req_info.append(self.SubInfo[i])
                        req_id.append(i) #dont need it
        testing=[]
        lessdis=[]
        trfNumber=1
        for x in range(len(req_info)):
            for j in range(len(req_info[x])):
                if j != 0:
                    
                    if j %2 ==0:
                        j+=1
                    if j == len(req_info[x]):
                        trfNumber=1
                        lessdis.append("NextBlock")
                        testing.append("NextBlock")
                        break
                    if req_info[x][j] in testing:
                        continue  
                    dlat=radians(float(self.ETCS_lastinfo[0][1]))-radians(float(req_info[x][j]))
                    dlon = radians(float(self.ETCS_lastinfo[0][2]))-radians(float(req_info[x][j+1]))
                    V1=2 * asin(sqrt(sin(dlat / 2)**2 + cos(float(req_info[x][j])) * cos(float(self.ETCS_lastinfo[0][1])) * sin(dlon / 2)**2))
                    d = 6371 * V1
                   
                    lessdis.append(d)
                    lessdis.append(req_info[x][0])
                    lessdis.append(trfNumber)
                    testing.append(trfNumber)
                    trfNumber+=1
                    
                    testing.append(req_info[x][j])
                    testing.append(req_info[x][j+1])
        del lessdis[-1] #delete last NextBlock 
        if "NextBlock" in lessdis:
            index=lessdis.index("NextBlock")
            new_list = lessdis[index+1:]
        else:
            new_list = lessdis
            index=-1
        
        
        cou=0

        min=lessdis[0]
        Name_Number_OFTRF=[]
        for x in range(len(lessdis)):
                if cou >= len(lessdis):
                    break
                if min > lessdis[cou]:
                        min=lessdis[cou]
                cou+=3
                if cou == index: #if NextBlock equal this cou
                    minindex=lessdis.index(min)
                    print("sending to "+str(lessdis[minindex+1])+" block to traffic number "+str(lessdis[minindex+2]))
                    Name_Number_OFTRF.append(lessdis[minindex+1])
                    Name_Number_OFTRF.append(lessdis[minindex+2])
                    
                    cou+=1
                    min=lessdis[cou]  
        #last block work
        minindex=lessdis.index(min)
        print("sending to "+str(lessdis[minindex+1])+" block to traffic number "+str(lessdis[minindex+2]))
        Name_Number_OFTRF.append(lessdis[minindex+1])
        Name_Number_OFTRF.append(lessdis[minindex+2])           
        pas=Passed(Name_Number_OFTRF,testing,self.ETCS_lastinfo)
        mqttcall=mqttPUB(Name_Number_OFTRF,0,0)
        mqttcall.PUB()
        print("Req for Traffics Done!")
        print("Waiting...")
        while 1:
            ch=pas.checkForPass()
            if ch ==0:
                mqttcallpassed=mqttPUB(Name_Number_OFTRF,5,0)
                mqttcallpassed.PUB()
                print("Back all traffics to normal...")
                break
        



class Passed: #Passed used to check if Emg car passed one of traffics if so use Mqtt broker to send to all of traffics to back to normal 
    def __init__(self,Name_Number_OFTRF,trf_points,ETCS_lastinfo):
        self.Name_Number_OFTRF=Name_Number_OFTRF
        self.trf_points=trf_points
        self.ETCS_lastinfo=ETCS_lastinfo
        self.tc=0
        self.nt=0

    def checkForPass(self):
        cou=[]
        indices = []
        ind=self.trf_points.index("NextBlock")
        indices = [index for index, element in enumerate(self.trf_points) if element == "NextBlock"] #to have index of the end of the block
        
        block=self.trf_points[ind+1:]
        
        for i in range(len(self.Name_Number_OFTRF)):
            if i % 2 != 0: 
                    for x in range(len(self.trf_points)):
                        if self.Name_Number_OFTRF[i] == self.trf_points[x]:
                            cou.append(self.trf_points[x+1])
                            cou.append(self.trf_points[x+2])
                            
        pi=0
        flag=0
        list=cou
        final=[]
        final1=[]
        
       
        dis_move=[]
        twoids=[]
        twoids.append(self.ETCS_lastinfo)
        while 1:
                
                iniWORK.backupDB()
                time.sleep(4.5)
                info=main("TrafficLights.txt","http://localhost/postdata.php",sys.argv[1])
                final1=info.trf_INFOS
                newinfo=info.new_get_REGEX()
                if newinfo != "No data":
                    break
               
        
          
            
        twoids.append(newinfo) #now have last locations
        self.ETCS_lastinfo=twoids[-1] #to update to last info
        

        
        j=0
        theblockids=[]
       
        
        q=0
        fg=1
        while fg:
            if fg==0:
                break
            for x in range(len(final1)):

                if final1[x][0] == self.Name_Number_OFTRF[q]:
                    final.append(final1[x][1])
                    final.append(final1[x][2])
                    q+=2
                    
                if len(self.Name_Number_OFTRF)==q:
                    fg=0
                    break    
            
        j=0
        
        while 1:
            dis_move.clear()
            if len(final)==4:
                if j >=2:
                    break
            if len(final)==2:
                if j>=1:
                    break
            for i in range(len(twoids)):# 0 1 2 3
                               
                              
                                dlat=radians(float(final[j]))-radians(float(twoids[i][0][1]))
                                dlon = radians(float(final[j+1]))-radians(float(twoids[i][0][2]))
                                V1=2 * asin(sqrt(sin(dlat / 2)**2 + cos(float(twoids[i][0][1])) * cos(float(final[j])) * sin(dlon / 2)**2))
                                
                                
                                d = 6371 * V1
                                dis_move.append(d)
                                

                                
                                if len(dis_move)==2:
                                    
                                    
                                    if dis_move[-1]>dis_move[-2]:
                                        #it must moved through traffic light
                                        if j==0:
                                            print("The EMG car moved through "+str(self.Name_Number_OFTRF[j])+" Traffic so Back Everything to Normal Situation")
                                        else:
                                            print("The EMG car moved through "+str(self.Name_Number_OFTRF[j+1])+" Traffic so Back Everything to Normal Situation")
                                        print("Back to normal")
                                        
                                        return 0
                                    
            j+=1                       
                                
                               
                                
        return 1
                       
       

class mqttPUB: #mqttPUB used to publish message to wanted traffic light who has subscribe to specific topic(block name)
    
    def __init__(self,Name_Number_OFTRF,tc,nt) :
        self.Name_Number_OFTRF=Name_Number_OFTRF
        self.tc=tc
        self.nt=nt
        self.broker = 'broker.emqx.io'
        self.port = 1883
        self.username = 'emqx'
        self.password = 'public'
        self.q=0
    def PUB(self):
               
                if self.nt % 2 !=0:
                    self.topic =self.Name_Number_OFTRF[self.nt+1] 
                else:
                    self.topic =self.Name_Number_OFTRF[self.nt]
                # generate client ID with pub prefix randomly
                client_id = f'python-mqtt-{random.randint(0, 1000)}'
               
                self.nt+=1

                def connect_mqtt():
                    def on_connect(client, userdata, flags, rc):
                        """
                        if rc == 0:
                            print("Connected to MQTT Broker!")
                        else:
                            print("Failed to connect, return code %d\n", rc)
                        """
                    client = mqtt_client.Client(client_id)
                    client.username_pw_set(self.username, self.password)
                    client.on_connect = on_connect
                    client.connect(self.broker, self.port)
                    return client


                def publish(client):
                    if len(self.Name_Number_OFTRF) ==2:
                        time.sleep(1)
                        if self.tc == 5:
                            msg=0
                        elif self.tc % 2 != 0:
                            msg=self.Name_Number_OFTRF[self.tc]
                        else:
                            msg=self.Name_Number_OFTRF[self.tc+1]
                        if self.topic == "Qassabah" and msg==0:
                            pass
                        else:    
                            result = client.publish(self.topic, msg)
                        # result: [0, 1]
                            status = result[0]
                            if status == 0:
                             print(f"Send `{msg}` to topic `{self.topic}`")
                             
                                 

                            else:
                             print(f"Failed to send message to topic {self.topic}")
                       
                        self.tc+=1
                    else:
                        for i in range(len(self.Name_Number_OFTRF)):
                            time.sleep(1)
                            if i % 2 !=0:
                                continue
                            if self.tc == 5:
                                msg=0
                            elif self.tc % 2 != 0:
                                msg=self.Name_Number_OFTRF[i]
                                
                            else:
                                msg=self.Name_Number_OFTRF[i+1]
                            if self.topic == "Qassabah" and msg==0:
                                pass   
                            else:   
                                result = client.publish(self.topic, msg)
                                # result: [0, 1]
                                status = result[0]
                                if status == 0:
                                    print(f"Send `{msg}` to topic `{self.topic}`")
                                    
                                else:
                                    print(f"Failed to send message to topic {self.topic}")
                                self.nt+=1
                                if i*2 >= len(self.Name_Number_OFTRF):
                                    break
                                if self.nt % 2 !=0:
                                    self.topic =self.Name_Number_OFTRF[self.nt+1] 
                                else:
                                    self.topic =self.Name_Number_OFTRF[self.nt]



                def run():
                    client = connect_mqtt()
                    client.loop_start()
                    publish(client)


                if __name__ == '__main__':
                    run()





while len(sys.argv) ==1:
    print("get help! -->python [scriptname].py Wanted_ID")
    exit()

#first we call class main with file name of trfs info and url that we need with regexp and cli of id    
informations=main("TrafficLights.txt","http://localhost/postdata.php",sys.argv[1])
meters=1

while 1:
    rege=informations.get_REGEX()
    if rege=="work":
        iniWORK=work(informations.reqid_INFOS ,informations.ids, informations.trf_INFOS)
        Flag=iniWORK.findDistance()
        
        if Flag ==1:
            iniWORK.backupDB()  
        else:
            less1Km=worklessthan1Km(informations.reqid_INFOS,informations.trf_INFOS,meters,iniWORK.tmpDistnace)
            less1Km.lessthan1Km(len(iniWORK.tmpDistnace))
            if meters == 3:
                meters=1
            else:
                meters+=1
            while 1:
                iniWORK.backupDB()
                newinfo=informations.new_get_REGEX()
                if newinfo != "No data":
                    
                    break
            
             
        
        continue  
