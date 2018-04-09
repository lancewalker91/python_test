#!/usr/bin/env python3
"""
    输入为文件名，内容每一行为：course_id plan_id filename
    把源文件，ftp传输到指定服务器
    """

import sys
import subprocess
import os
import shlex

g_ftp_params = {"host":"222.247.50.156", "user":"cjwx_wlyy", "passwd":"wlyy9632", "timeout":30}


def transfer_one_file(course_id, plan_id, one_file):
    local_file = one_file
    ftp_file = "{course_id}-{plan_id}-{filename}".format(course_id=course_id, plan_id=plan_id, filename=os.path.basename(one_file))
    cmd = "ncftpput -C -m -u {user} -p {passwd} -t {timeout}  {host} {local_file} {ftp_file}".format(ftp_file=ftp_file, local_file=local_file, **g_ftp_params)
    print("cmd = [{}]".format(cmd))
    ret = subprocess.call(shlex.split(cmd), stdout=None, stderr=subprocess.STDOUT)
    if ret:
        print("fails")

def deal_files(filename):
    for line in open(filename):
        items = line.strip().split()
        if 3 == len(items):
            transfer_one_file(*items)

if "__main__" == __name__:
    if len(sys.argv) != 2:
        sys.exit("argv: filename")

    deal_files(sys.argv[1])
