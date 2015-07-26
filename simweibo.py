# -*- coding: utf-8 -*-
'''
Created on 6 Aug, 2014

@author: burkun
'''
import urllib2, urllib
from pyquery import PyQuery as pyq 
import re, json, base64
import rsa, binascii, time
import pickle, os, random
from cookielib import CookieJar



class Log():
    @staticmethod
    def cur_time(pre):
        return "[" + time.strftime("%Y-%m-%d %H:%M:%S" ,time.localtime(time.time())) + " "+pre+"] "
    @staticmethod
    def info(msg, mtype = "info"):
        f = open("log.txt", "wb")
        f.write(Log.cur_time(mtype) + msg.encode("utf-8") + "\n")
        f.close()
    @staticmethod
    def error(msg):
        Log.info(msg, "error")



url_prelogin = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo'\
'&callback=sinaSSOController.preloginCallBack&su=%s&rsakt=mod&client=ssologin.js(v1.4.18)'\
'&_=1364875106625'
url_comment = 'http://weibo.com/aj/v6/comment/small'
url_home_pattern = 'http://weibo.com/u/%s/home'
class Weibo(object):
    
    def fecth_page(self, url='http://weibo.com', data=None):
        return self.__opener.open(url, data)
    
    def __init__(self, username, password):
        self.__username = username
        self.__password = password
        self.__uid = None
        self.__nickname = None
        self.__commentCache = None
        old_cj =  self.__read_cj() 
        if old_cj is not None:
            Log.info("use old cookie!")
            self.__cj = old_cj
        else:
            Log.info("use new cookie")
            self.__cj = CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.__cj))
        opener.addheaders =  [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0') \
                                    , ("Referer", ("http://weibo.com/u/%s/home?wvr=5" % self.__uid)) \
                                    ,('Content-type', "application/json")]
        self.__opener = opener
        if old_cj is None:
            Log.info("cookie is none or expire! need login!")
            self.__login()
            self.__write_cj()
            
        
    
    def __write_cj(self):
        #include cookie jar
        Log.info("cache cookie, the next time will auto login!")
        dd = {"cookies": [c for c in self.__cj], "uid" : self.__uid, "nick" : self.__nickname}
        pickle.dump(dd, open("cookiejar.dat", "w"))
    
    def __read_cj(self):
        MAX_EPS = 86400 #24 hours
        if os.path.exists("cookiejar.dat"):
            modtime = os.stat("cookiejar.dat").st_mtime
            if time.time() - modtime > MAX_EPS:
                return None
            else:
                dd = pickle.load(open("cookiejar.dat", "r"))
                cj =  CookieJar()
                for c in dd["cookies"]:
                    cj.set_cookie(c)
                self.__uid = dd["uid"]
                self.__nickname = dd["nick"]
                return cj
        else:
            return None
        #f = open("opener.dat", "w");
    
    def __loadcomment(self):
        if os.path.exists("comm.pickle"):
            Log.info("load cache...")
            f = open("comm.pickle")
            self.__commentCache = pickle.load(f)
            f.close()
    
    def __writecomment(self):
        if len(self.__commentCache) > 0:
            Log.info("write cache...")
            f = open("comm.pickle", "w")
            pickle.dump(self.__commentCache, f)
            f.close()
    
    def __encode_passwd(self, pwd, servertime, nonce, pubkey):
        rsaPublickey = int(pubkey, 16)
        key = rsa.PublicKey(rsaPublickey, 65537)  
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(pwd)  
        passwd = rsa.encrypt(message, key)
        passwd = binascii.b2a_hex(passwd)
        return passwd

    def __nick_name(self):
        resp = self.__opener.open(url_home_pattern % self.__uid)
        html = resp.read()
        nick_pattern = "$CONFIG['nick']='"
        idx = html.find(nick_pattern)
        idx += len(nick_pattern)
        begin = idx
        while html[idx] != "'":
            idx += 1
        return html[begin : idx]
        
    def __encode_username(self, username):
        username = bytes(urllib.quote(username))
        username = base64.encodestring(username)[:-1]
        return username
    
    def __cur_str_date(self):
        return "["+time.strftime("%Y-%m-%d %H:%M:%S" ,time.localtime(time.time()))+"]"
    
    def __prelogin(self, su):
        pre_login = url_prelogin % su
        html = self.__opener.open(pre_login).read()
        json_data = re.search('\((.*)\)', html).group(1)
        data = json.loads(json_data)
        if data["retcode"] == 0:
            servertime = data['servertime']
            nonce = data['nonce']
            pubkey = data['pubkey']
            rsakv = data['rsakv']
            exectime = data['exectime']
            pcid = data["pcid"]
        else:
            raise Exception("Someting wrong in prelogin!")
        return servertime, nonce, pubkey, rsakv, exectime, pcid
    
    def __login(self):
        url_login = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
        su = self.__encode_username(self.__username)
        (servertime, nonce, pubkey, rsakv, dummy_exectime, dummy_pcid) = self.__prelogin(su)
        sp = self.__encode_passwd(self.__password, servertime, nonce, pubkey)
        postdata = {
                    'entry': 'weibo',
                    'gateway': 1,
                    'from': '',
                    'savestate': 7,
                    'userticket': 1,
                    'ssosimplelogin': '1',
                    'vsnf': '1',
                    'vsnval': '',
                    'su': su,
                    'service': 'miniblog',
                    'servertime': servertime,
                    'nonce': nonce,
                    'pwencode': 'rsa2',
                    'sp': sp,
                    'encoding': 'UTF-8',
                    'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
                    'returntype': 'META',
                    'rsakv' : rsakv,
                    }


        postdata = urllib.urlencode(postdata).encode("utf-8")
        html = self.__opener.open(url_login, postdata).read().decode('gbk')
        url_final = re.search('location\.replace\([\"|\'](.*?)[\"|\']\)', html).group(1)
        reason = url_final.split("reason=")
        if len(reason) == 2:
            reason = reason[1]
        else:
            reason = "login success!"
        Log.info(reason)
        loginpage = self.__opener.open(url_final)
        self.__get_uid(loginpage.read())
        self.__nickname = self.__nick_name()
        #add global header

    def __get_rnd(self):
        return str(int(time.time() * 1000000))
    
    def post_text(self, text):
        url_post = 'http://weibo.com/aj/mblog/add?_wv=5&__rnd='
        post_data = {
                    'text':text  + " "+self.__cur_str_date(),
                    'pic_id':'',
                    'rank':0,
                    'rankid':'',
                    '_surl':'',
                    'hottopicid':'',
                    'location':'home',
                    'module':'stissue',
                    '_t':0,
            }
        
        postdata = urllib.urlencode(post_data)
        html = self.__opener.open(url_post + self.__get_rnd(), postdata).read()
        data = json.loads(html)
        if data["code"] == "100000":
            Log.info("post text is done!")
        else:
            Log.error("post fail!")
            Log.error(html)
         
    def __get_uid(self, loginok_html):
        self.__uid = re.search('"uniqueid":"(\d+)"', loginok_html).group(1)
        
    
    
    
    def get_comment(self, mid):
        postdata = {
        'ajwvr' : 6,
        'act' : 'list',
        'mid' : None,
        'uid' : None,
        'isMain': 'true',
        'dissDataFromFeed': '%5Bobject%20Object%5D',
        'ouid' : None,
        'location':'v6_content_home',
        'comment_type':1,
        '_t' : 0,
        '__rnd':None
        }
        postdata['mid'] = mid
        postdata['uid'] = self.__uid
        postdata['ouid'] = self.__uid
        postdata['__rnd'] = self.__get_rnd()
        postdata = urllib.urlencode(postdata).encode("utf-8") #必须是get方法
        html = self.__opener.open(url_comment+ "?" + postdata).read()
        return self.__parse_commentJson(html)
        
    
    def __parse_commentJson(self, json_html):
       
        data = json.loads(json_html)
        try:
            htmldata = data['data']['html']
            #print htmldata
            content = pyq(htmldata)
            divs = content.find('div[node-type="feed_list_commentList"] .list_li')
            res = {}
            for div in divs:
                commid = div.attrib['comment_id']
                comments = div.cssselect(".WB_text")
                for com in comments:
                    res[commid] =  com.text_content().strip()
            return res
        except Exception, e:
            Log.error(e)
        
    def get_new_post_comment(self, mid):
        if self.__commentCache is None:
            self.__loadcomment()
        data = self.get_comment(mid)
        if data is not None:
            notinpost = {}
            if self.__commentCache is None:
                notinpost = data
                self.__commentCache = data
            else:
                for key in data:
                    if key not in self.__commentCache:
                        notinpost[key] = data[key]
                        self.__commentCache[key] = data[key]
            self.__writecomment()
        postStr = []
        for key in notinpost:
            line = notinpost[key]
            idx = line.find(u"：")
            if idx != -1:
                uname = line[0: idx]
                content = line[idx+1 :]
                postStr.append((uname, content))
        return postStr
            
    def uploadJpegImg(self, imgPath):
        Log.info("upload image...")
        req = UploadImg.getJpegRequest(imgPath, self.__uid, self.__nickname)
        resp = self.__opener.open(req)
        html = resp.read()
        matches = re.search('.*"code":"(.*?)".*"pid":"(.*?)"', html)
        if matches.group(1)  == "A00006":
            Log.info("upload success!")
            pid = matches.group(2)
            Log.info("image id : "+ pid)
            return pid
        else:
            Log.error("post fail!")
            Log.error(html)
            return None

    def postTextWithImage(self, text, jpgpath):
        POST_URL = "http://weibo.com/aj/mblog/add?ajwvr=6&__rnd= %s" % str(self.__get_rnd())
        pid = self.uploadJpegImg(jpgpath)
        post_data = {
                       "location":"v6_content_home",
                       "appkey": "",
                       "style_type": 1,
                       "pic_id" : pid,
                       "text" : text + " "+self.__cur_str_date(), 
                       'pdetail' : "",
                       "rank" : "0",
                       "rankid": "",
                       "module" : "stissue",
                       "pub_type" : "dialog",
                       "_t" : 0}
        req = self.__buildPostTextImageRequest(POST_URL, post_data)
        #print req.get_full_url()
        resp = self.__opener.open(req)
        html = resp.read()
        data = json.loads(html)
        if data["code"] == "100000":
            Log.info("post text image is ok!")
        else:
            Log.error("post fail!")
            Log.error(html)
        
    def __buildPostTextImageRequest(self, url, data):
        return urllib2.Request(url, urllib.urlencode(data).encode("utf-8"))
class UploadImg():
    VIEW_URL = "http://ww2.sinaimg.cn/mw1024/%s.jpg"
    APIURL = 'http://picupload.service.weibo.com/interface/pic_upload.php?app=miniblog&data=1'
    MAXPICNUM = 9
    MAXSIZE = 20971520
    @staticmethod
    def getUniqueKey():
        b = time.time() * 1000
        return b
    
    @staticmethod
    def getRandom():
        return random.random()
    
    @staticmethod
    def getBuildRequet(uid, nick='某白鱼'):
        return {
                    'url' : 'weibo.com/u/' + str(uid),
                    'markpos' : 1,
                    'logo' : 1,
                    'nick' : nick,
                    'marks' : 1,
                    'mime' : 'image/jpeg',
                    'ct' : UploadImg.getRandom(),
                }
    @staticmethod
    def buildRequest(url, data):
        return urllib2.Request(UploadImg.APIURL + "&" + url, data, headers={'Content-type': "application/octet-stream", 
        "Referer":"http://js.t.sinajs.cn/t6/home/static/swf/MultiFilesUpload.swf?version=1c4459ee3b69aae4",
        "X-Requested-With":"ShockwaveFlash/17.0.0.188",
        "Accept-Encoding":"gzip, deflate",
        "Connection":"keep-alive",
        "Content-Length":len(data),
        'Host':'picupload.service.weibo.com'})
        
    @staticmethod   
    def ensmbelUrl(data):
        res = ""
        for key in data:
            res += str(key) + "=" + str(data[key]) + "&"
        return res[0 : len(res) - 1]
    
    @staticmethod
    def getJpegRequest(imgpath, uid, nick):
        urldata = UploadImg.getBuildRequet(uid, urllib.quote(nick))
        enurl = UploadImg.ensmbelUrl(urldata)
        f = open(imgpath, 'rb')
        data = f.read()
        f.close()
        if len(data) > UploadImg.MAXSIZE:
            Log.info("image size to large!")
            return None
        else:
            return UploadImg.buildRequest(enurl, data)

     
if __name__ == '__main__':
    pass
    #weibo = Weibo('burkun', '******')
    #print weibo.uploadJpegImg("../test.JPG")
    #weibo.postTextWithImage("机器发的第一个带图片的微博!!!很兴奋呐!!!", "../test.JPG")
    #weibo.decide_post_comment();
    #weibo.get_comment('3856489792158325')
    
    #UploadImg.getJpegRequest("../test.JPG", "1502371603", "某白鱼")
