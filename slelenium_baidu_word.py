# !/usr/bin/python
# -*- coding: utf-8 -*-

from selenium import webdriver
# 进入浏览器设置
options = webdriver.ChromeOptions()
# 设置中文
options.add_argument('lang=zh_CN.UTF-8')
# 更换头部
options.add_argument('user-agent="Mozilla/5.0 (Linux; U; Android 4.4.4; zh-cn; SM-G7508Q Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko)Version/4.0 MQQBrowser/5.7 Mobile Safari/537.36"')
browser = webdriver.Chrome(chrome_options=options)
url = "https://wenku.baidu.com/view/aa31a84bcf84b9d528ea7a2c.html"
browser.get(url)
browser.find_element_by_xpath('/html/body/div/div[2]/div[6]/div[2]/div[16]/div[1]/div/div[1]')


