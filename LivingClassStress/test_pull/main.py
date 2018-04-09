#!/usr/bin/env python3
"""
    测试pull收消息。
    list -- 列出所有的plan
    list plan -- 列出一个plan的消息对比
    clear plan -- 清除一个plan的历史消息
    add plan -- 增加一个plan
    del plan -- 删除一个plan
    """

from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler
from tornado import gen
from tornado.websocket import websocket_connect
from tornado.httpserver import HTTPServer
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
import os
import requests


g_default_port = 9021
g_ws_url = "ws://dev.gn100.com:8001/message.plan.ws"
g_pull_url = "http://dev.gn100.com:8001/message.plan.pull"


class OnePlanPull():
    def __init__(self, pool, plan_id, index):
        self.pool = pool
        self.plan_id = plan_id
        self.index = index
        self.data = {"text":{}, "signal":{}, "good":{}}
        self._id = {"text":0, "signal":0, "good":0}
        self.live = True
    @gen.coroutine
    def deal_result(self, request):
        request["StartTextId"] = self._id["text"]
        request["StartSignalId"] = self._id["signal"]
        request["StartGoodId"] = self._id["good"]
        text = json.dumps(request, separators=(",",":"))
        url = "{url}?callback=pull_callback&data={data}".format(url=g_pull_url, data=text)
        print("url=[{}]".format(url))
        r = yield self.pool.submit(requests.get, url)
        r.encoding = "utf8"
        print("r.text=[{}]".format(r.text))
        if len(r.text) > 16:
            data = json.loads(r.text[14:-2])
            for i in data:
                if "text" == i["mt"]:
                    self.data["text"][i["st"]] = i
                    self._id["text"] = i["st"]
                elif "signal" == i["mt"]:
                    self.data["signal"][i["ss"]] = i
                    self._id["signal"] = i["ss"]
                elif "good" == i["mt"]:
                    self.data["good"][i["sg"]] = i
                    self._id["good"] = i["sg"]
    @gen.coroutine
    def start(self):
        token = "p{:04d}".format(self.index)
        request = {"MessageType":"get", "UserIdFrom":0, "UserFlagFrom":token, "PlanId":self.plan_id, "StartTextId":0, "StartSignalId":0, "StartGoodId":0, "TextLimit":-1}
        yield self.deal_result(request)
        del request["TextLimit"]
        while self.live:
            yield self.deal_result(request)
        self.pool.shutdown()
    def clear(self):
        self.data["text"] = {}
        self.data["signal"] = {}
        self.data["good"] = {}
    def end(self):
        self.live = False


class OnePlanWs():
    def __init__(self, plan_id, index):
        self.plan_id = plan_id
        self.index = index
        self.data = {"text":{}, "signal":{}, "good":{}}
        self.live = True
    @gen.coroutine
    def start(self):
        token = "w{:04d}".format(self.index)
        request = {"MessageType":"get", "UserIdFrom":0, "UserFlagFrom":token, "PlanId":self.plan_id, "StartTextId":0, "StartSignalId":0, "StartGoodId":0, "TextLimit":-1}
        text = json.dumps(request, separators=(",",":"))
        self.conn = yield websocket_connect(g_ws_url)
        self.conn.write_message(text)
        self.heart_beat()
        while self.live:
            msg = yield self.conn.read_message()
            print("msg=[{}]".format(msg))
            if msg:
                data = json.loads(msg)
                for i in data:
                    if "text" == i["mt"]:
                        self.data["text"][i["st"]] = i
                    elif "signal" == i["mt"]:
                        self.data["signal"][i["ss"]] = i
                    elif "good" == i["mt"]:
                        self.data["good"][i["sg"]] = i
    @gen.coroutine
    def heart_beat(self):
        yield gen.sleep(10)
        while self.live:
            self.conn.write_message("{}")
            yield gen.sleep(10)
    def clear(self):
        self.data["text"] = {}
        self.data["signal"] = {}
        self.data["good"] = {}
    def end(self):
        self.conn.close()
        self.live = False


class OnePlan():
    def __init__(self, plan_id, ws_num, pull_num):
        self.plan_id = plan_id
        self.ws_num = ws_num
        self.wss = []
        for i in range(ws_num):
            one = OnePlanWs(plan_id, i)
            self.wss.append(one)
        self.pull_num = pull_num
        self.pool = ThreadPoolExecutor(pull_num)
        self.pulls = []
        for i in range(pull_num):
            one = OnePlanPull(self.pool, plan_id, i)
            self.pulls.append(one)
    @gen.coroutine
    def start(self):
        for i in self.wss:
            i.start()
        for i in self.pulls:
            i.start()
    def clear(self):
        for i in self.wss:
            i.clear()
        for i in self.pulls:
            i.clear()
    def end(self):
        self.websocket.end()
        for i in self.pulls:
            i.end()
    def get_one_diff(self, data1, data2):
        result = {}
        for i in ("text", "signal", "good"):
            a = set(data1[i].keys()).symmetric_difference(set(data2[i].keys()))
            #print("diff:",set(data1[i].keys()))
            if a:
                data = {}
                for j in a:
                    if j in data1[i]:
                        data["+{}".format(j)] = data1[i][j]
                    else:
                        data["-{}".format(j)] = data2[i][j]
                result[i] = data
        return result
    def get_diff(self):
        ws = self.wss[0]
        data1 = []
        for i in self.wss[1:]:
            data = self.get_one_diff(ws.data, i.data)
            if data:
                data1.append(data)
        data2 = []
        for i in self.pulls:
            data = self.get_one_diff(ws.data, i.data)
            if data:
                data2.append(data)
        data = {}
        if data1:
            data["ws"] = data1
        if data2:
            data["pull"] = data2
        return data


class BaseHandler(RequestHandler):
    pass


class MainHandler(BaseHandler):
    def get(self):
        self.render("main.html")


class ControlHandler(WebSocketHandler):
    help_str = """usage:
        list -- 列出所有的在用的plan
        list plan -- 列出一个plan的情况
        clear plan -- 清除一个plan的缓存
        add plan ws_num pull_num -- 增加一个plan，指定ws和pull模式客户端个数
        del plan -- 删除一个plan
        """
    plans = {}
    def open(self):
        pass
    def on_message(self, message):
        if "help" == message:
            self.write_message(self.help_str)
        elif "list" == message:
            return self.deal_list()
        elif message.startswith("list"):
            return self.deal_list_plan(message)
        elif message.startswith("clear"):
            return self.deal_clear(message)
        elif message.startswith("add"):
            return self.deal_add(message)
        elif message.startswith("del"):
            return self.deal_del(message)
    def on_close(self):
        pass
    def check_origin(self, origin):
        print("origin=[{}]".format(origin))
        return True
    @gen.coroutine
    def deal_add(self, message):
        items = message.split()
        if 4 != len(items):
            self.write_message("input = [{}] is error!".format(message))
            return
        plan_id = int(items[1])
        ws_num = int(items[2])
        pull_num = int(items[3])
        if plan_id in self.plans:
            self.write_message("plan_id = [{}] has existed!".format(plan_id))
            return
        one_plan = OnePlan(plan_id, ws_num, pull_num)
        self.plans[plan_id] = one_plan
        yield one_plan.start()
        self.write_message("ok")
    def deal_clear(self, message):
        items = message.split()
        if 2 != len(items):
            self.write_message("input = [{}] is error!".format(message))
            return
        plan_id = int(items[1])
        if plan_id in self.plans:
            self.plans[plan_id].clear()
            self.write_message("ok")
        else:
            self.write_message("no plan = [{}]".format(plan_id))
    def deal_del(self, message):
        items = message.split()
        if 2 != len(items):
            self.write_message("input = [{}] is error!".format(message))
            return
        plan_id = int(items[1])
        if plan_id in self.plans:
            one_plan = self.plans.pop(plan_id)
            one_plan.end()
            self.write_message("ok")
        else:
            self.write_message("no plan = [{}]".format(plan_id))
    def deal_list(self):
        data = []
        for k, v in self.plans.items():
            data.append("<p>{plan_id}: {ws} {pull}</p>".format(plan_id=k, ws=v.ws_num, pull=v.pull_num))
        self.write_message("".join(data))
    def deal_list_plan(self, message):
        items = message.split()
        if 2 != len(items):
            self.write_message("input = [{}] is error!".format(message))
            return
        plan_id = int(items[1])
        if plan_id in self.plans:
            one_plan = self.plans[plan_id]
            data = one_plan.get_diff()
            print("list plan, data=[{}]".format(data))
            self.write_message(json.dumps(data))
        else:
            self.write_message("no plan = [{}]".format(plan_id))


def main(port):
    setting = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        "autoreload": True,
        }
    app = Application([
        (r"/ws", ControlHandler),
        (r"/", MainHandler),
        ], **setting)
    HTTPServer(app).listen(port)
    IOLoop.current().start()


if "__main__" == __name__:
    from tornado.options import options, define, parse_command_line
    define("port", default=g_default_port, type=int, help="server port")
    parse_command_line()
    main(options.port)
