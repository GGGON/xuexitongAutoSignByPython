#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :sign.py
@说明    :学习通签到Python版本 支持 普通签到/照片签到/手势签到/定位签到
@时间    :2022/10/01 16:50
@作者    :DanceDJ
@微信公众号    :给我一碗炒饭
@其他    :推荐使用云签到哦，在公众号查看，代码写了很多注释，希望可以帮到大家
@版本    :2.1  群友改造
'''

import requests,json
import urllib.parse
from random import choices
import datetime,os,time
session = requests.session()
requests.packages.urllib3.disable_warnings()

#用户配置！必须写！
setting={
    "account":'', #账号（手机号 ）「必填」
    "password":'', #密码 「必填」
    "sign":{
        "long":'', #定位签到经纬度 「可空」
        "lat":'', #定位签到经纬度 「可空」
        "address":'', #定位签到显示的地址 「必填」
        "name":'', #签到姓名 「必填」
        "img":['4c57ab8d2d25b6a60bcbd102a094b1b0'], #图片自定义之后再写，这里可以自己填入objectId列表就可以了，默认上传的图片是「图片加载失败」用来迷惑老师
        "sign_common":True, #是否开启普通签到 「True 开启 False 关闭」 默认开启，无需修改
        "sign_pic":True,    #是否开启照片签到 「True 开启 False 关闭」 默认开启，无需修改
        "sign_hand":True,   #是否开启手势签到 「True 开启 False 关闭」 默认开启，无需修改
        "sign_local":True,  #是否开启定位签到 「True 开启 False 关闭」 默认开启，无需修改
    },
    "other":{
        "count":6, #每门课程只检测前N个活动 避免因课程活动太多而卡住
        "sleep":60 #每次检测间隔时间（S）默认60秒 一分钟
    }
}

#乱七八糟的变量 不要动我
mycookie=""
myuid=""
courselist=[]

#登录
def login(uname,code):
    global mycookie,myuid
    url="https://passport2-api.chaoxing.com/v11/loginregister?code="+code+"&cx_xxt_passport=json&uname="+uname+"&loginType=1&roleSelect=true"
    res=session.get(url)
    data = requests.utils.dict_from_cookiejar(session.cookies)
    mycookie=""
    for key in data:
        mycookie+=key+"="+data[key]+";"
    d=json.loads(res.text)
    if(d['mes']=="验证通过"):
        print(uname+"登录成功")
        url="https://sso.chaoxing.com/apis/login/userLogin4Uname.do"
        res=session.get(url)
        a=json.loads(res.text)
        if(a['result']==1):
            myuid=str(a['msg']['puid'])
            #save_cookies(myuid,2)
            return 1
        else:
            print("获取uid失败")
    return 0
#获取同意请求头 包含Cookie
def getheaders():
    headers={"Accept-Encoding": "gzip",
    "Accept-Language": "zh-Hans-CN;q=1, zh-Hant-CN;q=0.9",
    "Cookie": mycookie,
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 com.ssreader.ChaoXingStudy/ChaoXingStudy_3_4.8_ios_phone_202012052220_56 (@Kalimdor)_12787186548451577248",
    "X-Requested-With": "com.chaoxing.mobile",

             }
    # "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 com.ssreader.ChaoXingStudy/ChaoXingStudy_3_4.8_ios_phone_202012052220_56 (@Kalimdor)_12787186548451577248"
    return headers
def getheaders2():
    headers={"Accept": "*/*",
             "Accept-Encoding": "gzip,deflate",
             "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",

             "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; M2007J22C Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36 com.chaoxing.mobile/ChaoXingStudy_3_4.3.4_android_phone_494_27 (@Kalimdor)_d0037b51d800439894388df2d41ec6ef",
             "X-Requested-With": "XMLHttpRequest",
             'Referer':'',
             'Host': 'mobilelearn.chaoxing.com',
             "Cookie": mycookie,
             'Sec-Fetch-Site': 'same-origin',
             'Sec-Fetch-Mode': 'cors',
             'Sec-Fetch-Dest': 'empty',
             'Connection': 'keep-alive'
             }
    # "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 com.ssreader.ChaoXingStudy/ChaoXingStudy_3_4.8_ios_phone_202012052220_56 (@Kalimdor)_12787186548451577248"
    return headers
#获取课程列表
def getcourse():
    global courselist
    url="http://mooc1-api.chaoxing.com/mycourse/backclazzdata?view=json&rss=1"
    headers=getheaders()
    if(headers==0):
        return 0
    res=session.get(url,headers=headers)

    if('请重新登录' in res.text):
        print("Cookie已过期")
    else:
        d=json.loads(res.text)
        courselist=d['channelList']

        print("课程列表加载完成")
#普通签到
def sign1(referer,aid,uid,name):
    t=get_time()
    print(t+" 发现普通签到")
    name=urllib.parse.quote(name)
    url="https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId="+aid+"&uid="+uid+"&clientip=&latitude=-1&longitude=-1&appType=15&fid=0&name="+name
    headers = getheaders2()
    headers['Referer'] = referer
    ani_spider=session.get(referer,headers=headers)
    time.sleep(2)
    if(headers==0):
        return 0
    res=requests.get(url,headers=headers)
    if(res.text=="success"):
       time.sleep(60) 
       return 1
        
    else:
        return 0
#照片签到/手势签到
def sign2(referer,aid,uid,oid,name):
    t=get_time()
    print(t+" 发现照片签到/手势签到")
    name=urllib.parse.quote(name)
    url="https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId="+aid+"&uid="+uid+"&clientip=&useragent=&latitude=-1&longitude=-1&appType=15&fid=0&objectId="+oid+"&name="+name
    headers = getheaders2()
    headers['Referer'] = referer
    requests.get(referer,headers=headers)
    time.sleep(2)
    if(headers==0):
        return 0
    res=requests.get(url,headers=getheaders2())
    print(res.text)
    if(res.text=="success"):
        time.sleep(60)
        return 1
    else:
        return 0
#定位签到
def sign3(referer,aid,uid,lat,long,name,address):
    t=get_time()
    print(t+" 发现定位签到")
    name=urllib.parse.quote(name)
    address=urllib.parse.quote(address)
    ani_spider=session.get(referer,headers=getheaders2())
    url="https://mobilelearn.chaoxing.com/pptSign/stuSignajax?name="+name+"&address="+address+"&activeId="+aid+"&uid="+uid+"&clientip=&latitude="+lat+"&longitude="+long+"&latitude_gd="+lat+"&longitude_gd"+long+"&fid=0&appType=15&ifTiJiao=1"
    #url="https://mobilelearn.chaoxing.com/newsign/preSign?courseId=228288159&classId=62734634&activePrimaryId=8000039303851&general=1&sys=1&ls=1&appType=15&uid=150862179&isTeacherViewOpen=0"
    #print('----------------------')
    #print(url)
    headers=getheaders2()
    headers['Referer']=referer
   # print(headers)
    if(headers==0):
        return 0
    time.sleep(2)
    res=requests.get(url,headers=headers)
    #print(headers)
    print(res.text)
    if(res.text=="success"):
        time.sleep(60)
        return 1
       
    else:
        return 0
#获取签到类型
def get_sign_type(aid):

    url="https://mobilelearn.chaoxing.com/newsign/signDetail?activePrimaryId="+aid+"&type=1&"
    headers:{
      "User-Agent": "Mozilla/5.0 (iPad; CPU OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 ChaoXingStudy/ChaoXingStudy_3_4.3.2_ios_phone_201911291130_27 (@Kalimdor)_11391565702936108810"
    }
    res=requests.get(url,verify=False)
    d=json.loads(res.text)
    #print(res.text)

    if(d['otherId']==0):
        if(d['ifPhoto']==1):
            return 1
        else:
            return 2
    elif(d['otherId']==2):
        if(d['ifRefreshEwm']==1):
            return 3
        else:
            return 4
    elif(d['otherId']==3):
        return 6
    elif(d['otherId']==4):
        return 5
    elif(d['otherId']==5):
        return 5
    else:
        return 0
#统一签到入口
def sign(referer,aid,uid,name):
    #拍照签到 1 普通签到 2 定位签到 5 手势签到 6 
    activeType=get_sign_type(aid)
    if(activeType==1):#拍照签到
        images=setting['sign']['img']
        #未配置图片
        if(len(images)==0):
            signres=sign2(referer,aid,uid,"",name)
        else:
            nowimg=choices(images)[0]
            signres=sign2(referer,aid,uid,nowimg,name)
    elif(activeType==2):#普通签到
        signres=sign1(referer,aid,uid,name)
    elif(activeType==5):#位置签到
        signres=sign3(referer,aid,uid,setting['sign']['lat'],setting['sign']['long'],name,setting['sign']['address'])
    elif(activeType==6):#手势签到
        signres=sign2(referer,aid,uid,"",name)
    else:
        return -1
    print("签到结果"+str(signres))
    return signres
#获取用户活动列表
def gettask(courseId,classId,uid,cpi,name,sign_common,sign_pic,sign_hand,sign_local):
    time.sleep(2)
    try:
        #url="https://mobilelearn.chaoxing.com/ppt/activeAPI/taskactivelist?courseId="+courseId+"&classId="+classId+"&uid="+uid+"&cpi="+cpi
        url="https://mobilelearn.chaoxing.com/v2/apis/active/student/activelist?fid=0&courseId="+courseId+"&classId="+classId+"&showNotStartedActive=0&_=1663752482576"

        headers=getheaders()
        if(headers==0):
            return 0
        res=requests.get(url,headers=headers)
        #print(f"{name}:{res.text}")
        d=json.loads(res.text)


        if(d['result']==1):
            #data去掉
            activeList=d['data']['activeList']
           # print(activeList)

            count=0
            for active in activeList:
                status=active['status']
                activeType=active['activeType']
                aid=str(active['id'])
                #referer=active['url']
                referer="https://mobilelearn.chaoxing.com/newsign/preSign?courseId="+courseId+"&classId="+classId+"&activePrimaryId="+aid+"&general=1&sys=1&ls=1&appType=15&tid=&uid="+uid+"&ut=s"
                if(status!=1):
                    return 0
                if(activeType==1 and sign_pic==True):
                    sign(referer,aid,uid,name)
                if(activeType==2 and sign_common==True):
                    sign(referer,aid,uid,name)
                if(activeType==5 and sign_local==True):
                    sign(referer,aid,uid,name)
                if(activeType==6 and sign_hand==True):
                    sign(referer,aid,uid,name)
                count+=1
                if(count>=setting['other']['count']):
                    break
    except Exception as e:
        print(e)
#获取时间
def get_time():
    today = datetime.datetime.today()
    year = today.year
    month = today.month
    day= today.day
    hour= today.hour
    minute= today.minute
    second= today.second
    if(month<10):
        month="0"+str(month)
    if(day<10):
        day="0"+str(day)   
    date="["+str(year)+"."+str(month)+"."+str(day)+" "+str(hour)+":"+str(minute)+":"+str(second)+"]"
    return date
#初始化Cookies
def init_cookies():
    try:
        with open('cookies.txt','r') as f:
            data=f.read()
            f.close()
            if(len(data)<100):
                return 0
            return data
    except Exception as e:
        return 0
#初始化uid
def init_uid():
    try:
        with open('uid.txt','r') as f:
            data=f.read()
            f.close()
            if(len(data)<5):
                return 0
            return data
    except Exception as e:
        return 0
#初始化img
def init_img():
    print('你没有看错，我不想写了，时间紧迫，完了再更新图片上传')
#保存Cookies文件
def save_cookies(data,type):
    if(type==1):
        with open('cookies.txt','w') as f:
            f.write(data)
            f.close()
    else:
        with open('uid.txt','w') as f:
            f.write(str(data))
            f.close()
#初始化函数
def init2():
    global mycookie,myuid
    if(setting['account']=="" or setting['password']==""):
        print("未进行账号配置")
        return 0
    cookies=init_cookies()
    uid=init_uid()
    if(cookies==0 or uid==0):
        res=login(setting['account'],setting['password'])
        if(res==0):
            print("登录失败，请检查账号密码")
        else:
            save_cookies(mycookie,1)
            getcourse()


    return 1

#初始化函数
def init():
    global mycookie,myuid

    res=login(setting['account'],setting['password'])
    if(res==0):
            print("登录失败，请检查账号密码")
    else:
        #    save_cookies(mycookie,1)
            getcourse()



    return 1
#检测函数    
def check():
    for course in courselist:

        if('roletype' in course['content']):
            roletype=course['content']['roletype']
        else:
            continue
        if(roletype!=3):
            continue

        classId=str(course['content']['id'])
        courseId=str(course['content']['course']['data'][0]['id'])
        cpi=str(course['content']['cpi'])
        gettask(courseId,classId,myuid,cpi,setting['sign']['name'],setting['sign']['sign_common'],setting['sign']['sign_pic'],setting['sign']['sign_hand'],setting['sign']['sign_local'])

if __name__ == "__main__":
    res=init()
    datetime1=datetime.datetime
    if(res==1):
        print("初始化完成")
        #课程开始时间 自行修改
        startTime=datetime1.strptime("07:30", "%H:%M")- datetime1.strptime('0:0', "%H:%M")
        #课程结束时间 自行修改
        endTime=datetime1.strptime("21:30", "%H:%M")- datetime1.strptime('0:0', "%H:%M")
        while True:

            now = datetime1.now()
            Time = now.strftime("%H:%M")
            Time = datetime1.strptime(Time, "%H:%M") - datetime1.strptime('0:0', "%H:%M")
            if(endTime>Time>startTime):
             check()
             #print(f"{endTime>Time>startTime}")
             time.sleep(setting['other']['sleep'])
            else:
                time.sleep(15)