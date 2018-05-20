from selenium import webdriver
import time
from selenium.webdriver.common.action_chains import ActionChains


def main():
    login()
    search_ticket()
    book_ticket()


def login():
    driver.get(url)
    driver.implicitly_wait(30)
    # 登陆账号
    username = driver.find_element_by_id('username')
    username.clear()
    username.send_keys(uname)
    # 登陆密码
    password = driver.find_element_by_id('password')
    password.clear()
    password.send_keys(pwd)

    while True:  # 手动进行图片验证，并登录
        curpage_url = driver.current_url
        print(curpage_url)
        if curpage_url != url:
            print('.......登陆成功........')
            break
        else:
            time.sleep(10)
            print('--------->等待用户进行图片验证')


def search_ticket():
    driver.find_element_by_link_text('车票预订').click()
    time.sleep(3)
    # 输入出发地
    driver.add_cookie({"name": "_jc_save_fromStation", "value": '%u5317%u4EAC%2CBJP'})  # 北京
    # 选择目的地
    driver.add_cookie({"name": "_jc_save_toStation", "value": '%u6B66%u6C49%2CWHN'})  # 武汉
    #  %u5E7F%u5DDE%u5357%2CIZQ(广州南)   %u8861%u9633%2CHYQ(衡阳)  %u6DF1%u5733%2CSZQ(深圳)

    # 选择出发日期
    driver.add_cookie({"name": "_jc_save_fromDate", "value": '2018-06-15'})
    driver.refresh()


def book_ticket():
    query_time = 0
    time_begin = time.time()
    # 循环查询
    while True:
        time.sleep(1)
        search_btn = driver.find_element_by_link_text('查询')
        search_btn.click()

        # 扫描查询结果
        try:
            driver.implicitly_wait(10)

            ticket_ele = driver.find_element_by_xpath('//*[@id="YW_2400000Z530R"]')  # 所抢车次对应的座位等级的xpath
            ticket_info = ticket_ele.text
            print(ticket_info)
        except:
            search_btn.click()
            driver.implicitly_wait(5)
            ticket_ele = driver.find_element_by_xpath('//*[@id="YW_2400000Z530R"]')
            ticket_info = ticket_ele.text
            print('可能您的xpath选择错误')

        if ticket_info == '无' or ticket_info == '--':
            query_time += 1
            cur_time = time.time()
            print('第{}次查询，用时{}秒' .format(query_time, cur_time - time_begin))
        else:
            driver.find_element_by_xpath('//*[@id="ticket_2400000Z530R"]/td[13]').click()
            break

    cust_url = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
    while True:
        if (driver.current_url == cust_url):
            print('页面跳至选择乘客信息 成功')
            break
        else:
            time.sleep(1)
            print('等待页面跳转')

    while True:
        try:
            driver.find_element_by_xpath('//*[@id="normalPassenger_0"]').click()  # _0是联系人列表里的第一个 ，依此类推
            break
        except:
            print('等待常用联系人列表')

    # 提交订单
    driver.find_element_by_xpath('//*[@id="submitOrder_id"]').click()

    # 确认订票信息
    while True:
        try:
            driver.switch_to.frame(driver.find_element_by_xpath('/html/body/iframe[2]'))
            print
            driver.find_element_by_xpath('//*[@id="qr_submit_id"]')
            print('pass')
        except:
            print('请手动选座和点击确认信息')
            time.sleep(5)
            break


if __name__ == '__main__':
    driver = webdriver.Firefox()
    url = 'https://kyfw.12306.cn/otn/login/init'
    uname = '17600117243'
    pwd = 'lt639607'
    main()