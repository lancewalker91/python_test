#!/usr/bin/env python3
#-*- encoding: utf8 -*-

"""
    模仿一个学生上课
    """

import requests
from tornado import gen
from tornado.websocket import websocket_connect
import json
import traceback
import random
from concurrent.futures import ThreadPoolExecutor

g_login_url = "http://dev.gn100.com/site.main.login"
g_add_msg_url = "http://dev.gn100.com/message.plan.add"
g_ws_url = "ws://dev.gn100.com:8001/message.plan.ws"

class Message:
    text = 1
    call = 6
    reply = 7
    microphone_test = 700
    fullscreen = 800
    microphone_result = 1012
    issue_ask = 1016
    issue_answer = 1018
    gift = 1040

class Client:
    """
        模仿一个学生。
        """
    #所有实例存储的地方。{plan_id:{user:[client, client, ...]}, ...}
    members = {}
    #为了节省内存，存储字符串的地方
    data = {}
    _answer =""
    block_pool = ThreadPoolExecutor(6)
    cpu_pool = ThreadPoolExecutor(1)
    @staticmethod
    def get_string(d):
        s = json.dumps(d, separators=(",",":"))
        if s in Client.data:
            return Client.data[s]
        else:
            Client.data[s] = s
            return s
    @classmethod
    def del_client(cls, plan_id, user):
        if plan_id in cls.members and user in cls.members[plan_id]:
            c = cls.members[plan_id][user].pop()
            c.close()
            if cls.members[plan_id][user]:
                del cls.members[plan_id][user]
    @classmethod
    def get_clients(cls):
        data = []
        for plan_id in cls.members:
            num = len(cls.members[plan_id])
            if num > 0:
                data.append("{plan_id}: {num}".format(plan_id=plan_id, num=num))
        if data:
            return "\n".join(data)
        else:
            return "None"
    @classmethod
    def get_clients_by_plan(cls, plan_id):
        if plan_id in cls.members and cls.members[plan_id]:
            data = []
            o = cls.members[plan_id]
            for user in o:
                data2 = []
                for c in o[user]:
                    if c.token:
                        data2.append("{user_id}: {token}".format(user_id=c.user_id, token=c.token))
                    else:
                        data2.append("init")
                data.append("{user}:\n\t{content}".format(user=user, content="\n\t".join(data2)))
            return "\n".join(data)
        else:
            return "None"
    @classmethod
    def get_clients_by_phone(cls, plan_id, phone):
        if plan_id in cls.members and phone in cls.members[plan_id]:
            data = []
            for c in cls.members[plan_id][phone]:
                if c.token:
                    data.append("{user_id}:{token}".format(user_id=c.user_id, token=c.token))
                else:
                    data.append("init")
            return "{phone}\n\t{data}".format(phone=phone, data="\n\t".join(data))
        else:
            return "None"
    @classmethod
    def get_clients_by_token(cls, plan_id, phone, token):
        if plan_id in cls.members and phone in cls.members[plan_id]:
            for c in cls.members[plan_id][phone]:
                if c.token and c.token.startswith(token):
                    buf = "ss: {ss}\n\tsg: {sg}\n\tst: {st}".format(ss=len(c.ss), sg=len(c.sg), st=len(c.st))
                    return "plan_id={plan_id}\tphone:{phone}\ttoken={token}\n\t{buf}".format(plan_id=plan_id, phone=phone, token=token, buf=buf)
            else:
                return "None for token={}".format(token)
        else:
            return "None"
    @classmethod
    def get_clients_ss(cls, plan_id, phone, token, ss, start=0, end=-1):
        if plan_id in cls.members and phone in cls.members[plan_id]:
            for c in cls.members[plan_id][phone]:
                if c.token and c.token.startswith(token):
                    if "ss" == ss:
                        buf = "{ss}:{data}".format(ss=ss, data="\n\t\t".join(c.get_ss(start, end)))
                    elif "sg" == ss:
                        buf = "{ss}:{data}".format(ss=ss, data="\n\t\t".join(c.get_sg(start, end)))
                    elif "st" == ss:
                        buf = "{ss}:{data}".format(ss=ss, data="\n\t\t".join(c.get_st(start, end)))
                    else:
                        buf = "ss:{data1}\n\tsg={data2}\n\tst={data3}".format(data1="\n\t\t".join(c.get_ss(start, end)), data2="\n\t\t".join(c.get_sg(start, end)), data3="\n\t\t".join(c.get_st(start, end)))
                    return "plan_id={plan_id}\tphone:{phone}\ttoken={token}\n\t{buf}".format(plan_id=plan_id, phone=phone, token=token, buf=buf)
            else:
                return "None for token={}".format(token)
        else:
            return "None"
    @classmethod
    def text(cls, plan_id, phone, token, repeat, start, end, content,live_second=0):
        if plan_id in cls.members and phone in cls.members[plan_id]:
            for c in cls.members[plan_id][phone]:
                if c.token.startswith(token):
                    c.add_msg_repeat(Message.text, 0, "", content, repeat, start, end,live_second)
                    break
    @classmethod
    def texts(cls, plan_id, phone, num, repeat, start, end, content,live_second=0):
        if plan_id in cls.members:
            for i in range(num):
                if phone+i in cls.members[plan_id]:
                    for c in cls.members[plan_id][phone+i]:
                        c.add_msg_repeat(Message.text, 0, "", content, repeat, start, end,live_second)
    @classmethod
    def gift(cls, plan_id, phone, token,content,start,end,live_second=0):
        if plan_id in cls.members and phone in cls.members[plan_id]:
            for c in cls.members[plan_id][phone]:
                if c.token.startswith(token):
                    c.add_msg_repeat(Message.gift,0, "", content, 1, start, end,live_second)
                    break
    
    @classmethod
    def gifts(cls, plan_id, phone, num,content, start,end,live_second=0):
        if plan_id in cls.members:
            for i in range(num):
                if phone+i in cls.members[plan_id]:
                    for c in cls.members[plan_id][phone+i]:
                        c.add_msg_repeat(Message.gift,0, "", content, 1, start, end,live_second)
    
    @classmethod
    def answer(cls,a):
        if a.find(";") > 0:
            cls._answer = a.split(";")
        else:
            cls._answer = a
    def __init__(self, user, passwd, plan_id, log_func):
        self.user = user
        self.passwd = passwd
        self.plan_id = plan_id
        self.log_func = log_func
        self.conn = False
        self.s = False
        self.user_id = 0
        self.token = ""
        self.ss = []
        self.sg = []
        self.st = []
        self.live = True
        self.add_client();
    def add_client(self):
        if self.plan_id not in Client.members:
            Client.members[self.plan_id] = {}
        data = Client.members[self.plan_id]
        if self.user in data:
            data[self.user].append(self)
        else:
            data[self.user] = [self, ]
    def login(self):
        try:
            r = self.s.post(g_login_url, data={"uname":self.user, "password":self.passwd,"submit":"登录","cid":1,"areaCode":86,"areaId":86})
            r.encoding = "utf8"
            if r.text:  #"基础资料" in r.text and "我的订单" in r.text and "安全设置" in r.text and "退出" in r.text:
                return True, r
            else:
                return False, r
        except Exception:
            print("fail with exception")
            print(traceback.format_exc())
            return False, False
    @gen.coroutine
    def add_msg(self, seconds, msg_type, to_id, to_token, content,live_second=0):
        print("add msg, type=[{}] content=[{}]".format(msg_type, content))
        yield gen.sleep(seconds)
        def add_msg_internal():
            data = {"plan_id":self.plan_id, "type":msg_type, "user_from_id":self.user_id, "user_from_token":self.token,"live_second":live_second}
            if 100 == msg_type:
                data["message_type"] = "good"
            elif msg_type in (1, 500):
                data["message_type"] = "text"
            else:
                data["message_type"] = "signal"
            if to_id:
                data["user_to_id"] = to_id
            if to_token:
                data["user_to_token"] = to_token
            if content:
                data["content"] = "{}".format(content)
            text = json.dumps(data, separators=(",",":"))
            print("add msg, text=[{}]".format(text))
            self.conn.write_message(text)
            #self.s.post(g_add_msg_url, data)
        yield Client.block_pool.submit(add_msg_internal)
    @gen.coroutine
    def add_msg_repeat(self, msg_type, to_id, to_token, content, repeat, start, end,live_second=0):
        for i in range(repeat):
            seconds = start + (end-start)*random.random()
            #content_new = content + str(i)
            live_second= live_second + seconds
            print("content:{},live_second:{}".format(content,live_second))
            yield self.add_msg(seconds, msg_type, to_id, to_token, content,live_second)
    @gen.coroutine
    def heart_beat(self):
        yield gen.sleep(10)
        while not self.conn.closed:
            self.conn.write_message("{}")
            yield gen.sleep(10)
    @gen.coroutine
    def start(self):
        while True:
            self.s = requests.Session()
            yield Client.block_pool.submit(self.login)
            a = self.s.cookies.get("uid_dev")
            if not a:
                yield gen.sleep(3)
                self.log_func("login fails for {}".format(self.user))
                continue
            self.user_id = int(a)
            self.token = self.s.cookies.get("token_dev")
            print("login uid:{},token:{}".format(self.user_id,self.token))
            self.websocket()
            break
    @gen.coroutine
    def websocket(self):
        request = {"MessageType":"get", "UserIdFrom":self.user_id, "UserFlagFrom":self.token[:5], "PlanId":self.plan_id, "StartTextId":0, "StartSignalId":0, "StartGoodId":0}
        while self.live:
            try:
                self.conn = yield websocket_connect(g_ws_url)
            except Exception:
                self.log_func("****************************************")
                self.log_func(traceback.format_exc())
                yield gen.sleep(3)
                continue
            # self.log_func("user={user} user_id={user_id} token={token} connect succeed!".format(user=self.user, user_id=self.user_id, token=self.token))
            self.conn.closed = False
            text = json.dumps(request, separators=(",",":"))
            # print("text=[{}]".format(text))
            self.conn.write_message(text)
            self.heart_beat()
            self.add_msg(0.01, Message.fullscreen, 0, "", 1)
            msg_times = 0
            ss_start = 0
            sg_start = 0
            st_start = 0
            while self.live:
                msg = yield self.conn.read_message()
                if not msg:
                    # self.log_func("user={user} user_id={user_id} token={token} colsed!".format(user=self.user, user_id=self.user_id, token=self.token))
                    self.conn.closed = True
                    break
                #print("msg=[{}]".format(msg))
                if len(msg) > 1024:
                    items = yield Client.cpu_pool.submit(json.loads, msg)
                else:
                    items = json.loads(msg)
                for i in items:
                    if "mt" not in i:
                        continue
                    if "text" == i["mt"]:
                        if i["st"] <= request["StartTextId"]:
                            if msg_times > 1 and i["st"] > st_start:
                                #self.log_func("{user} {token} {start} {times} text error for {rst} {st}".format(user=self.user, token=self.token, start=st_start, times=msg_times, rst=request["StartTextId"], st=i["st"]))
                                pass
                        else:
                            request["StartTextId"] = i["st"]
                        self.st.append(self.get_string(i))
                    elif "signal" == i["mt"]:
                        if i["ss"] <= request["StartSignalId"]:
                            if msg_times > 1 and i["ss"] > ss_start:
                                #self.log_func("{user} {token} {start} {times} signal error for {rss} {ss}".format(user=self.user, token=self.token, start=ss_start, times=msg_times, rss=request["StartSignalId"], ss=i["ss"]))
                                pass
                        else:
                            if msg_times > 0 and i["ss"] > ss_start:
                                if request["StartSignalId"]+1 != i["ss"]:
                                   #self.log_func("{user} {token} {start} {times} signal2 error for {rss} {ss}".format(user=self.user, token=self.token, start=ss_start, times=msg_times, rss=request["StartSignalId"], ss=i["ss"]))
                                    pass
                            request["StartSignalId"] = i["ss"]
                            if msg_times > 2 :
                                if 0 == i["ut"] or (self.user_id == i["ut"] and self.token.startswith(i["uft"])):
                                    if Message.call == i["ct"]:
                                        seconds = 3 + 2 * random.random()
                                        self.add_msg(seconds, Message.reply, 0, "", "")
                                    elif Message.microphone_test == i["ct"]:
                                        seconds = 10 + 5 * random.random()
                                        self.add_msg(seconds, Message.microphone_result, 0, "", "fail")
                                    elif Message.issue_ask == i["ct"]:
                                        if Client._answer:
                                            if type(Client._answer) is list :
                                                seconds = 5 + 5 * random.random()
                                                c = {"id":json.loads(i["c"])["id"], "answer":random.choice(Client._answer)}
                                                self.add_msg(seconds, Message.issue_answer, 0, "", json.dumps(c))
                                            else :
                                                seconds = 5  + 5 * random.random()
                                                c = {"id":json.loads(i["c"])["id"], "answer":Client._answer}
                                                self.add_msg(seconds, Message.issue_answer, 0, "", json.dumps(c))
                        self.ss.append(self.get_string(i))
                    elif "good" == i["mt"]:
                        if i["sg"] <= request["StartGoodId"]:
                            if msg_times > 1 and i["sg"] > sg_start:
                                #self.log_func("{user} {token} {start} {times} good error for {rsg} {sg}".format(user=self.user, token=self.token, start=sg_start, times=msg_times, rsg=request["StartGoodId"], sg=i["sg"]))
                                pass
                        else:
                            request["StartGoodId"] = i["sg"]
                        self.sg.append(self.get_string(i))
                msg_times += 1
                if 1 == msg_times:
                    ss_start = request["StartSignalId"]
                    sg_start = request["StartGoodId"]
                    st_start = request["StartTextId"]
    def close(self):
        # print("client close start")
        self.live = False
        if self.conn and not self.conn.closed:
            self.conn.close()
        if self.s:
            self.s.close()
        # print("client close end")
    def clear_ss(self):
        self.ss = []
    def clear_st(self):
        self.st = []
    def clear_sg(self):
        self.sg = []
    def clear(self):
        self.ss = []
        self.st = []
        self.sg = []
    def get_ss(self, start, end):
        if end < 0:
            end = len(self.ss)
        return self.ss[start:end]
    def get_st(self, start, end):
        if end < 0:
            end = len(self.st)
        return self.st[start:end]
    def get_sg(self, start, end):
        if end < 0:
            end = len(self.sg)
        return self.sg[start:end]
    def test():
        for plan_id in Client.members:
            for user in Client.members[plan_id]:
                for c in Client.members[plan_id][user]:
                    c.add_msg(1, 1, 0, "", "test")

def main(data):
    from tornado.ioloop import IOLoop
    from concurrent.futures import ThreadPoolExecutor
    thread_pool = ThreadPoolExecutor(4)
    client = Client(data["user"], data["passwd"], data["plan_id"], thread_pool.submit, print)
    client.start()
    IOLoop.current().start()

if "__main__" == __name__:
    from tornado.options import options, define, parse_command_line
    define("user", default="18888880000", type=str, help="phone")
    define("passwd", default="18888880000", type=str, help="passwd")
    define("plan_id", default=840, type=int, help="plan id")
    parse_command_line()
    main(options)
