#!/usr/bin/env python3
#-*- encoding: utf8 -*-

import requests
import login
import json

g_reg_url = "http://dev.gn100.com/course/info/addreg"

def free_reg(s, course_id, class_id):
    r = s.post(g_reg_url, data={"cid":course_id,"classId":class_id,"oid":0,"source":1})
    r.encoding = "utf8"
    return r

def reg_one(user, passwd, course_id, class_id):
    s = requests.Session()
    a, _ = login.login(s, user, passwd)
    if not a:
        print("phone=[{user}] login fails".format(user=user))
        return 1
    r = free_reg(s, course_id, class_id)
    #print(r)
    a = r.json()
    print(a)
    if 0 == a["code"]:
        return 0
    else:
        print("phone=[{user}] err=[{err}]".format(user=user, err=a))
        return 1

if '__main__' == __name__:
    import argparse
    parser = argparse.ArgumentParser(description="免费报名")
    parser.add_argument("user", type=str, help="用户名")
    parser.add_argument("passwd", type=str, help="密码")
    parser.add_argument("course_id", type=int, help="课程id")
    parser.add_argument("class_id", type=int, help="班级id")
    args = parser.parse_args()
    r = reg_one(args.user, args.passwd, args.course_id, args.class_id)
    print("result = [{}]".format(r))

