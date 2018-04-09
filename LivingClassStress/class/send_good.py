#!/usr/bin/env python3
"""
    给一个plan_id下的所有学生发点赞信息（多次）
    """

import requests
import pymysql
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler
from tornado import gen
from tornado.websocket import websocket_connect
import json

g_login_url = "http://hetao.gn100.com/site.main/login"
g_ws_url = "ws://dev.gn100.com:8001/message.plan.ws"
g_db = {"host":"127.0.0.1", "user":"root", "passwd":"", "db":"db_course", "charset":"utf8", "cursorclass":pymysql.cursors.DictCursor}


def get_users_from_plan(plan_id):
    with pymysql.connect(**g_db) as cursor:
        sql = "select fk_class from t_course_plan where pk_plan={plan_id}".format(plan_id=plan_id)
        print(sql)
        cursor.execute(sql)
        row = cursor.fetchone()
        if not row:
            return
        sql = "select fk_user from t_course_user where fk_class={class_id}".format(class_id=row["fk_class"])
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            return
        return [row["fk_user"] for row in rows]


def login(phone, passwd):
    s = requests.Session()
    r = s.post(g_login_url, data={"uname":phone, "password":passwd,"areaId":86,"areaCode":86,"cid":1,"submit":"登录"})
    user_id = int(s.cookies.get("uid_hetao"))
    token = s.cookies.get("token_hetao")
    return user_id, token


@gen.coroutine
def add_msg(ws, plan_id, user_id, token, to_id, to_token, msg_type, content):
    data = {"plan_id":plan_id, "type":msg_type, "user_from_id":user_id, "user_from_token":token}
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
        data["content"] = content
    text = json.dumps(data, separators=(",",":"))
    #print("add msg={}".format(text))
    ws.write_message(text)


@gen.coroutine
def read_msg(ws):
    while True:
        msg = yield ws.read_message()
        print("lishenghong:{}".format(msg))

@gen.coroutine
def goods(students, plan_id, user_id, token, num):
    ws = yield websocket_connect(g_ws_url)
    request = {"MessageType":"get", "UserIdFrom":user_id, "UserFlagFrom":token[:5], "PlanId":plan_id, "StartTextId":0, "StartSignalId":0, "StartGoodId":0}
    text = json.dumps(request, separators=(",",":"))
    ws.write_message(text)
    read_msg(ws)
    print("start good")
    n = 0
    for _ in range(num):
        for i in students:
            print("i=[{}] n=[{}]".format(i, n))
            n += 1
            add_msg(ws, plan_id, user_id, token, i, "", 100, "1")
            yield gen.sleep(0.0001)


def main(plan_id, num, teacher_phone, passwd):
    #print(plan_id,num,teacher_phone,passwd)
    students = get_users_from_plan(plan_id)
    #students = [22410, 5302, 5303, 6302]
    #students = [6303,6302]
    #print("students={}".format(students))
    user_id, token = login(teacher_phone, passwd)
    print("teacher id:{};token:{}".format(user_id,token))
    for i in range(1):
        goods(students, plan_id, user_id, token, num)
    IOLoop.current().start()


if "__main__" == __name__:
    from tornado.options import options, define, parse_command_line
    define("plan_id", type=int, help="plan_id")
    define("num", default=1, type=int, help="num")
    define("phone", type=str, help="teacher_phone")
    define("passwd", type=str, help="password")
    parse_command_line()
    main(options.plan_id, options.num, options.phone, options.passwd)

