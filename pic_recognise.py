# -*- coding: utf-8 -*-

import cookielib
import hashlib
import urllib
import urllib2
import uuid
import requests
import time
import random
import sys

class Ucode(object):
    def __init__(self, softId, softKey, user, pwd,codeType):
        # self.logger = logging.getLogger('PicRecognise')
        self.softId = softId
        self.softKey = softKey
        self.user = user
        self.pwd = pwd
        self.codeType=codeType
        self.uid = "100"
        self.initUrl = "http://common.992U.com:9090/Service/ServerConfig.aspx"
        self.version = '1.0.0.1'
        self.cookieJar = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar))
        self.loginUrl = None
        self.uploadUrl = None
        self.codeUrl = None
        self.params = []
        self.uKey = None

    def initialise(self):
        flag = False
        try:
            params = self.initHeader()
            if params:
                self.params = params
                self.opener.addheaders = params
                response = self.opener.open(self.initUrl, None, 30)
                if response.code == 200:
                    body = response.read()
                    if body is not None and len(body) > 0:
                        body = body.strip()
                        if body.find(",") != -1:
                            bs = body.split(",")
                            if bs is not None:
                                if len(bs) >= 4:
                                    self.loginUrl = bs[1][:-4]
                                    self.uploadUrl = bs[2][:-4]
                                    self.codeUrl = bs[3][:-4]
                                    flag = True
        except Exception as e:
            print "Error:can't initialise api"
            print e
        return flag

    def login(self):
        flag = True
        if self.loginUrl is not None:
            try:
                mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
                self.params.append(('KEY', self.md5(self.softKey.upper() + self.user.upper()) + mac))
                self.params.append(('UUKEY',self.md5(self.user.upper()+mac+self.softKey.upper())))
                self.opener.addheaders = self.params
                url = "http://" + self.loginUrl
                url += "/Upload/Login.aspx?U=%s&p=%s" % (self.user, self.md5(self.pwd))
                try:
                    response = self.opener.open(url, None, 60)
                    if response.code == 200:
                        body = response.read()
                        if body is not None:
                            if body.find("-") > 0:
                                us = body.split("_")
                                self.uid = us[0]
                                self.uKey = body.strip()
                                print u'登录成功，用户ID是：',self.uid
                                flag = True
                            else:
                                print u'登录失败,错误代码是：',body
                                flag = False
                except Exception, e:
                    print "Error:Login Request"
                    print e
            except Exception, e:
                print "Error:Login Params "
                print e
        return flag

    #def

    def upload(self, fileAddress=None,filemem=None):
        code = None
        if self.uKey is not None:
            try:
                image = open(fileAddress, 'rb')
                data = {'KEY': self.uKey,
                        "SID": self.softId,
                        'SKey': self.md5((self.uKey + self.softId + self.softKey).lower()),
                        'Type': self.codeType}  #codetype及价格表详见.http://www.uuwise.com/price.html
                url = "http://" + self.uploadUrl + "/Upload/Processing.aspx"
                req = requests.post(url, data=data, files={'IMG': image}, timeout=60)
                if req.status_code == 200:
                    body = req.text
                    if body is not None:
                        print u'图片已上传，返回验证码ID：',body
                        code = self.result(str(body))
                        print u'正在获取识别结果...'
                        while (code == '-3'):
                                sys.stdout.write('.')
                                time.sleep(1)
                                code = self.result(str(body))
            except Exception, e:
                print e
        return code

    def result(self, body):
        code = None
        params = {'KEY': self.uKey, 'ID': body, 'random': (str(random.randint(1, 1000000)) + str(int(time.time())))}
        url = "http://" + self.codeUrl + "/Upload/GetResult.aspx?" + urllib.urlencode(params)
        response = self.opener.open(url, None, 30)
        if response.code == 200:
            code = response.read()
        return code

    def initHeader(self):
        ps = None
        try:
            ps = [('SID', self.softId),
                  ('HASH', self.md5(self.softId + self.softKey.upper())),
                  ('UUVersion', self.version),
                  ('UID', self.uid),
                  ('User-Agent', self.md5(self.softKey.upper() + self.uid))]
        except Exception, e:
            print "Error: can't make http header"
            print e
        return ps

    def md5(self, key):
        return hashlib.md5(key.encode(encoding='utf-8')).hexdigest()

class PicRecognise():
    def __init__(self):
        self.ucode = Ucode("109525", "3e5d3a91433148498af80f81aa3d4246", "guonana", "22cf2e77", "1004")
        if not self.ucode.initialise():
            raise NameError('uucloud init failed!')
        self.ucode.login()

    def PicRecognise(self, filename):
        return self.ucode.upload(filename)

if __name__ == '__main__':
    pr = PicRecognise()
    vcode = pr.PicRecognise("./image/vcode.jpg")
    print vcode
