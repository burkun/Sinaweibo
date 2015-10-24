
# -*- coding: utf-8 -*-
from simweibo import Weibo
from util import getImg
from simweibo import Log



if __name__ == '__main__':
    equalStrs =[u"请你吃饭", u"爱老虎油"]
    mid = '3858772139445809'
    #isok, imgpath = getImg()
    w = Weibo("*****", "***********")
    comms = w.get_new_post_comment(mid)
    if len(comms) == 0:
        Log.info("no one comment!")
    else:
        normalUser = set()
        specialUser = set()
        for item in comms:
            if item[1].find(equalStrs[0]) != -1:
                normalUser.add(item[0])
            if item[1].find(equalStrs[1]) != -1:
                specialUser.add(item[0])
        res = ""
        for u in normalUser:
            if len(res) < 250:
                res += "@" + u
            else:
                break
        for u in specialUser:
            if len(res) < 250:
                res += "@" + u 
            else:
                break
        Log.info("send weibo " + res)
        isok, imgpath = getImg()
        w.postTextWithImage(res.encode("utf-8"), imgpath)
        Log.info("session done!")
        
