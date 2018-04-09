#!/usr/bin/env python3
#-*- encoding: utf8 -*-

import free_reg
import argparse

def work(num, start, course_id, class_id):
    fails = 0
    for i in range(num):
        phone = str(start+i)
        #fails += free_reg.reg_one(phone, phone, course_id, class_id)
        password ="111111" 
        fails += free_reg.reg_one(phone, password, course_id, class_id)
    return fails

if '__main__' == __name__:
    parser = argparse.ArgumentParser(description="免费报名(重复报名)")
    parser.add_argument("num", type=int, help="个数")
    parser.add_argument("start", type=int, help="开始手机号（用18888880000-18888884999）")
    parser.add_argument("course_id", type=int, help="课程id")
    parser.add_argument("class_id", type=int, help="班级id")
    args = parser.parse_args()
    r = work(args.num, args.start, args.course_id, args.class_id)
    print("fails = [{}]".format(r))
