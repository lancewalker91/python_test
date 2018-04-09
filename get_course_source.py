#!/usr/bin/env python3
"""
    输入course_id，得到源文件地址，
    输出为： course_id plan_id source_file
    """

import sys
import pymysql

g_db = {"host":"", "user":"", "passwd":"", "db":"db_course", "charset":"utf8", "cursorclass":pymysql.cursors.DictCursor}

def deal_one_course(course_id):
    with pymysql.connect(**g_db) as cursor:
        sql = "select pk_plan from t_course_plan where fk_course={}".format(course_id)
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            return
        plans = [row["pk_plan"] for row in rows]
        for plan_id in plans:
            sql = "select filename from db_live.t_live_upload_file where fk_plan={}".format(plan_id)
            cursor.execute(sql)
            rows = cursor.fetchall()
            if not rows:
                sql = "select filename from db_live.t_live_record_file where fk_plan={}".format(plan_id)
                cursor.execute(sql)
                rows = cursor.fetchall()
            for row in rows:
                print("{course_id}\t{plan_id}\t{filename}".format(course_id=course_id, plan_id=plan_id, filename=row["filename"]))

if "__main__" == __name__:
    if len(sys.argv) < 2:
        sys.exit("argv: course_id(s)")

    for i in sys.argv[1:]:
        course_id = int(i)
        deal_one_course(course_id)
