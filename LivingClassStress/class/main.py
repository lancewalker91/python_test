#!/usr/bin/env python3
#-*- encoding: utf8 -*-

"""
    模仿多个学生上课
    """

import client
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler
import traceback
import os
import json
class ControlHandler(WebSocketHandler):
    help_str = """usage:
        add plan_id phone[ passwd[ num]] -- 一个学生上线（有num，表示多点登陆）
        adds plan_id phone_start num -- 多个学生上线
        del plan_id phone[ num] -- 一个学生下线（有num表示删除多个）
        dels plan_id phone num -- 多个学生下线
        list[ plan_id[ phone[ token[ ss|st|sg|all[ start[ end]]]]]] -- 列出内存内容
        text plan_id phone token repeat start end live_second content -- 发文本信息（发送时间为starth到end之间的随机数之后，发repeat次,live_second:距离视频开始时间）
        texts plan_id phone num repeat start end live_second content -- 发文本信息（发送从phone开始，连着num个手机号,live_second同上）
        answer[ answer] -- 设置答题的答案（没有参数表示不让答题,可以用分号分隔提交多个备选答案，逗号分隔表示多选（随机答一个））
        gift plan_id phone token  giftType gift_num  start end live_second --单个学生送鲜花 (giftType:礼物类型[鲜花:FLOWER],num:"礼物数量")
        gifts plan_id phone num  giftType gift_num start end live_second --批量学生送鲜花(num:学生数,其它同上)
        """
    members = []
    def log_write(buf):
        if ControlHandler.members:
            for i in ControlHandler.members:
                i.write_message(buf)
        else:
            print(buf)
    def open(self):
        ControlHandler.members.append(self)
        ControlHandler.log_write("new connection from {ip}".format(ip=self.request.remote_ip))
    def on_message(self, message):
        ControlHandler.log_write("echo cmd=[{cmd}] from {ip}".format(cmd=message, ip=self.request.remote_ip))
        if "help" == message:
            self.write_message(ControlHandler.help_str)
        elif "close" == message:
            IOLoop.current().stop()
        elif "test" == message:
            self.deal_test(message)
        elif message.startswith("add"):
            self.deal_add(message)
        elif message.startswith("del"):
            self.deal_del(message)
        elif message.startswith("list"):
            self.deal_list(message)
        elif message.startswith("text"):
            self.deal_text(message)
        elif message.startswith("answer"):
            self.deal_answer(message)
        elif message.startswith("gift"):
            self.deal_gift(message)
        else:
            self.write_message("donot recognize cmd={}".format(message))
    def on_close(self):
        ControlHandler.members.remove(self)
        ControlHandler.log_write("close connection from {ip}".format(ip=self.request.remote_ip))
    def check_origin(self, origin):
        print("origin=[{}]".format(origin))
        return True
    def deal_add(self, message):
        try:
            items = message.split()
            if "add" == items[0] and len(items) >= 3:
                plan_id = int(items[1])
                user = int(items[2])
                if len(items) > 3:
                    passwd = items[3]
                else:
                    passwd = user
                num = 1
                if len(items) > 4:
                    num = int(items[4])
                for i in range(num):
                    c = client.Client(user, passwd, plan_id, ControlHandler.log_write)
                    c.start()
            elif "adds" == items[0] and len(items) >= 4:
                plan_id = int(items[1])
                user = int(items[2])
                num = int(items[3])
                for i in range(num):
                    #c = client.Client(user+i, user+i, plan_id, ControlHandler.log_write)
                    c = client.Client(user+i,"111111", plan_id, ControlHandler.log_write)
                    c.start()
            else:
                self.write_message("add cmd=[{}] is error".format(message))
        except Exception:
            self.write_message("add message=[{}] is error,[{}]".format(message, traceback.format_exc()))
    def deal_del(self, message):
        try:
            items = message.split()
            if "del" == items[0] and len(items) >= 3:
                plan_id = int(items[1])
                user = int(items[2])
                if len(items) > 3:
                    num = int(items[3])
                else:
                    num = 1
                for i in range(num):
                    client.Client.del_client(plan_id, user)
            elif "dels" == items[0] and len(items) > 3:
                plan_id = int(items[1])
                user = int(items[2])
                num = int(items[3])
                for i in range(num):
                    client.Client.del_client(plan_id, user+i)
            else:
                self.write_message("del cmd=[{}] is error".format(message))
        except Exception:
            self.write_message("del message=[{}] is error,[{}]".format(message, traceback.format_exc()))
    def deal_list(self, message):
        try:
            items = message.split()
            if 1 == len(items):
                buf = client.Client.get_clients()
                self.write_message(buf)
            elif 2 == len(items):
                plan_id = int(items[1])
                buf = client.Client.get_clients_by_plan(plan_id)
                self.write_message(buf)
            elif 3 == len(items):
                plan_id = int(items[1])
                phone = int(items[2])
                buf = client.Client.get_clients_by_phone(plan_id, phone)
                self.write_message(buf)
            elif 4 == len(items):
                plan_id = int(items[1])
                phone = int(items[2])
                token = items[3]
                buf = client.Client.get_clients_by_token(plan_id, phone, token)
                self.write_message(buf)
            elif len(items) >= 5:
                plan_id = int(items[1])
                phone = int(items[2])
                token = items[3]
                ss = items[4]
                start = 0
                if len(items) > 5:
                    start = int(items[5])
                end = -1
                if len(items) > 6:
                    end = int(items[6])
                buf = client.Client.get_clients_ss(plan_id, phone, token, ss, start, end)
                self.write_message(buf)
            else:
                self.write_message("list cmd=[{}] is error".format(message))
        except Exception:
            self.write_message("list message=[{}] is error,[{}]".format(message, traceback.format_exc()))
    def deal_text(self, message):
        items = message.split(maxsplit=8)
        try:
            if len(items) == 9 and items[0] in ("text", "texts"):
                if "text" == items[0]:
                    plan_id = int(items[1])
                    phone = int(items[2])
                    token = items[3]
                    repeat = int(items[4])
                    if repeat < 0:
                        repeat = 0
                    start = float(items[5])
                    end = float(items[6])
                    if end < start:
                        end = start
                    live_second=int(items[7])
                    content = items[8]
                    client.Client.text(plan_id, phone, token, repeat, start, end, content,live_second)
                else:
                    plan_id = int(items[1])
                    phone = int(items[2])
                    num = int(items[3])
                    repeat = int(items[4])
                    if repeat < 0:
                        repeat = 0
                    start = float(items[5])
                    end = float(items[6])
                    if end < start:
                        end = start
                    live_second=int(items[7])
                    content = items[8]
                    client.Client.texts(plan_id, phone, num, repeat, start, end, content,live_second)
            else:
                self.write_message("text cmd=[{}] is error".format(message))
        except Exception:
            self.write_message("text message=[{}] is error,[{}]".format(message, traceback.format_exc()))
    def deal_answer(self, message):
        items = message.split(maxsplit=1)
        if 1 == len(items):
            client.Client.answer("")
        elif 2 == len(items):
            client.Client.answer(items[1])
        else:
            self.write_message("answer cmd=[{}] is error".format(message))
    
    def deal_gift(self, message):
        items = message.split(maxsplit=8)
        try:
            if len(items) == 9 and items[0] in ("gift", "gifts"):
                if "gift" == items[0]:
                    plan_id = int(items[1])
                    phone = int(items[2])
                    token = items[3]
                    giftType = items[4]
                    gift_number = int(items[5])
                    start = float(items[6])
                    end   = float(items[7])
                    live_second = float(items[8])
                    content = {"gift":giftType,"number":gift_number}
                    content = json.dumps(content,separators=(',',':'))
                    print("content:{}".format(content))
                    client.Client.gift(plan_id, phone, token,content,start,end,live_second)
                else:
                    plan_id = int(items[1])
                    phone = int(items[2])
                    num = int(items[3])
                    giftType = items[4]
                    gift_number = int(items[5])
                    start = float(items[6])
                    end   = float(items[7])
                    live_second = float(items[8])
                    content = {"gift":giftType,"number":gift_number}
                    content = json.dumps(content,separators=(',',':'))
                    print("content:{},live_second:{}".format(content,live_second))
                    client.Client.gifts(plan_id, phone,num,content,start,end,live_second)
            else:
                self.write_message("text cmd=[{}] is error".format(message))
        except Exception:
            self.write_message("text message=[{}] is error,[{}]".format(message, traceback.format_exc()))
  
    def deal_test(self, message):
        client.Client.test()

class MainHandler(RequestHandler):
    def get(self):
        self.render("clients.html")

def main(port):
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        "xsrf_cookies": True,
    }
    app = Application([
        (r"/ws", ControlHandler),
        (r"/", MainHandler),
        ], **settings)
    app.listen(port)
    IOLoop.current().start()

if "__main__" == __name__:
    from tornado.options import options, define, parse_command_line
    define("port", default=9102, type=int, help="port")
    parse_command_line()
    main(options.port)
