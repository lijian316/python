import time,random,re,json,requests,datetime
from selenium import webdriver
from selenium.webdriver import Chrome
import urllib.request


#微信公众号账号
user=""
#公众号密码
password=""
#设置要爬取的公众号列表
gzlist=['Meione-Media','gh_40518fc718bb']

# 登录
def weChat_login():
    #定义一个空的字典，存放cookies内容
    post={}
    #用webdriver启动谷歌浏览器
    print("STEP1:启动浏览器，打开微信公众号登录界面")
    driver = webdriver.Chrome()
    driver.get('https://mp.weixin.qq.com/')
    #等待5秒钟
    time.sleep(5)
    print("正在输入微信公众号登录账号和密码......")
    driver.find_element_by_xpath("./*//a[@class='login__type__container__select-type']").click()
    #清空账号框中的内容
    driver.find_element_by_xpath("./*//input[@name='account']").clear()
    #自动填入登录用户名
    driver.find_element_by_xpath("./*//input[@name='account']").send_keys(user)
    #清空密码框中的内容
    driver.find_element_by_xpath("./*//input[@name='password']").clear()
    #自动填入登录密码
    driver.find_element_by_xpath("./*//input[@name='password']").send_keys(password)
    # 在自动输完密码之后需要手动点一下记住我
    print("请在登录界面点击:记住账号")
    time.sleep(10)
    #自动点击登录按钮进行登录
    driver.find_element_by_xpath("./*//a[@title='点击登录']").click()
    # 拿手机扫二维码！
    print("请拿手机扫码二维码登录公众号")
    time.sleep(20)
    print("登录成功")
    #重新载入公众号登录页，登录之后会显示公众号后台首页，从这个返回内容中获取cookies信息
    driver.get('https://mp.weixin.qq.com/')
    #获取cookies
    cookie_items = driver.get_cookies()
    #获取到的cookies是列表形式，将cookies转成json形式并存入本地名为cookie的文本中
    for cookie_item in cookie_items:
        post[cookie_item['name']] = cookie_item['value']
    cookie_str = json.dumps(post)
    with open('cookie.txt', 'w+', encoding='utf-8') as f:
        f.write(cookie_str)
    print("cookies信息已保存到本地")


#爬取微信公众号文章，并存在本地文本中
def get_content(query):
    #query为要爬取的公众号名称
    #公众号主页
    url = 'https://mp.weixin.qq.com'
    #设置headers
    header = {
        "HOST": "mp.weixin.qq.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    }
    #读取上一步获取到的cookies
    with open('cookie.txt', 'r', encoding='utf-8') as f:
        cookie = f.read()
    cookies = json.loads(cookie)
    #登录之后的微信公众号首页url变化为：https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=1849751598，从这里获取token信息
    response = requests.get(url=url, cookies=cookies)
    token = re.findall(r'token=(\d+)', str(response.url))[0]
    #搜索微信公众号的接口地址
    search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
    #搜索微信公众号接口需要传入的参数，有三个变量：微信公众号token、随机数random、搜索的微信公众号名字
    query_id = {
        'action': 'search_biz',
        'token' : token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
        'random': random.random(),
        'query': query,
        'begin': '0',
        'count': '5'
    }
    #打开搜索微信公众号接口地址，需要传入相关参数信息如：cookies、params、headers
    search_response = requests.get(search_url, cookies=cookies, headers=header, params=query_id)
    #取搜索结果中的第一个公众号
    lists = search_response.json().get('list')[0]
    #获取这个公众号的fakeid，后面爬取公众号文章需要此字段
    fakeid = lists.get('fakeid')
    #微信公众号文章接口地址
    appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
    #搜索文章需要传入几个参数：登录的公众号token、要爬取文章的公众号fakeid、随机数random
    query_id_data = {
        'token': token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
        'random': random.random(),
        'action': 'list_ex',
        'begin': '0',#不同页，此参数变化，变化规则为每页加5
        'count': '5',
        'query': '',
        'fakeid': fakeid,
        'type': '9'
    }
    #每页至少有5条，获取文章总的页数，爬取时需要分页爬，但我的需求里只需要第一页的就行了所以不循环
    #获取当前页文章的标题和链接地址，并写入本地文本中
    query_fakeid_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=query_id_data)
    fakeid_list = query_fakeid_response.json().get('app_msg_list')
    today = int(time.mktime(datetime.date.today().timetuple()))
    for item in fakeid_list:
        if item.get('update_time')>=today:
            content_link=item.get('link')
            content_title=item.get('title')
            fileName=query+'.txt'
            with open(fileName,'a',encoding='utf-8') as fh:
                fh.write(content_title+":\n"+content_link+"\n")
    time.sleep(2)


# 爬取图片，防盗链处理 http://mmbiz.qpic.cn  替换为 http://read.html5.qq.com/image?src=forum&q=5&r=0&imgflag=7&imageUrl=http://mmbiz.qpic.cn
def get_pic(query):
    with open(query+'.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if "http" in line:
                print(line)
                # response = urllib.request.urlopen(line)
                # html = response.read().decode('utf-8')
                # soup = BeautifulSoup(html,'html.parser')
                # for k in soup.findall('img'):
                #     print(k['src']);                

if __name__=='__main__':
    try:
        # weChat_login()
        
        # for query in gzlist:
        #     print("开始爬取公众号：" + query)
        #     get_content(query)
        #     print("爬取完成")

        for query in gzlist:
            print("开始处理公众号：" + query)
            get_pic(query)
            print("处理完成")
        
    except Exception as e:
        print(str(e))