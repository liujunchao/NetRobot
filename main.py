import os
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from fileUtil import getVideoFiles,getAccounts,moveFile,removeLinkLine,getConfigByKey,removeAccountLine,convertList
from jiebaUtil import dividewords
from queue import Queue
import random

class NetbaseRobot:
    loginUrl = "http://dy.163.com/wemedia/login.html"
    accountList = []
    videoList = []
    videoIndex = 0
    articleList = []
    articleIndex = 0
    articleQueue =Queue()
    articleTitleDic = {}

    def __init__(self):
        self.accountList = getAccounts()
        self.videoList = getVideoFiles()
        linksContent = open("links.txt", encoding='utf-8').read()

        for link in linksContent.split("\n"):
            link = link.strip()
            if link == "":
                continue
            arr = convertList(link)
            self.articleQueue.put(arr[0])
            if len(arr)>1:
                self.articleTitleDic[arr[0]] = arr[1]
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 60)
        self.driver.maximize_window()
        self.downloadArticleOrNot()

    def downloadArticleOrNot(self):
        # self.driver.set_page_load_timeout(15)
        print("程序检查是否需要再下载文章，总共有"+ str(self.articleQueue.qsize()) +"文章没下载")
        while not self.articleQueue.empty() and len(self.articleList) - self.articleIndex<7:
            newLink = self.articleQueue.get()
            title, content = self.fetchLinksContent(newLink)
            if title == "" or content == "":
                removeLinkLine(newLink)
                continue
            self.articleList.append({"title": title, "content": content,"url":newLink})
        # self.driver.set_page_load_timeout(30)

    def login(self,idx):
        if len(self.accountList) <= idx:
            print("无法登陆了")
            return
        account = self.accountList[idx][0]
        pw = self.accountList[idx][1]
        print(account + " 准备登陆")
        self.driver.get(self.loginUrl)

        frame =self.wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'iframe')))
        # frame = self.driver.find_element_by_tag_name("iframe")
        id = frame.get_attribute("id")
        self.driver.switch_to.frame(id)
        nameElement = self.wait.until(EC.visibility_of_element_located((By.NAME, 'email')))
        # nameElement = self.driver.find_element_by_name("email")
        nameElement.clear()
        nameElement.send_keys(account)
        pwElement = self.driver.find_element_by_name("password")
        pwElement.clear()
        pwElement.send_keys(pw)
        loginButton = self.driver.find_element_by_id("dologin")
        loginButton.click()
        sleep(2)
        if "account-banned" in  self.driver.current_url:
            print(account +"帐号被禁了，程序会从account.txt中移除它")
            removeAccountLine(account,pw)
            self.turnToNextAccout(idx)
            return
        self.driver.execute_script("""
              if(document.getElementsByClassName("ne-confirm").length>0){
                  document.querySelector(".ne-btn-hollow").click();
              }
          """)
        # 发布文章
        while True:
            article = self.chooseArticle()
            if article is None:
                break
            isDone = self.doFormSubmit(article, account)
            if isDone == False:
                self.turnToNextAccout(idx)
                return
            else:
                self.articleIndex = self.articleIndex + 1

        # 发布视频
        while True:
            video = self.chooseVideo()
            if video is None:
                break
            isDone = self.submitVideoForm(video)
            if isDone == False:
                self.turnToNextAccout(idx)
                return
            else:
                self.videoIndex = self.videoIndex + 1

        print("操作结束,原因有可能是没有可更新的资源")
        self.driver.close()


    def turnToNextAccout(self,idx):
        sleep(1)
        if "account-banned" not in self.driver.current_url:
            self.logOut()
        idx = idx + 1
        if len(self.accountList) > idx:
            self.login(idx)
        else:
            print("帐号用完了，操作结束")
            self.driver.close()

    def chooseArticle(self):
        if self.articleIndex < len(self.articleList):
            return self.articleList[self.articleIndex]
        return None

    def chooseVideo(self):
        if self.videoIndex < len(self.videoList):
            return self.videoList[self.videoIndex]
        return None

    # 爬虫抓取文章内容
    def fetchLinksContent(self,link):
        print("开始下载文章"+link)
        httpIndex = link.find("http://")
        httpsIndex = link.find("https://")
        if httpIndex>0 or httpsIndex>0:
            link = link[httpsIndex+httpIndex+1:]
        self.driver.get(link)

        try:
            if "kuaibao.qq.com" in self.driver.current_url:
                titleElement = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'title')))
                self.driver.execute_script(
                    '$("#content").find(".title").remove();$("#content").find(".cardBoxWrap").remove();')
            elif "mbd.baidu.com" in self.driver.current_url:
                titleElement = self.driver.execute_script('return document.querySelector("h1")')
                if titleElement is None:
                    titleElement = self.driver.find_element_by_xpath("//span[@class='titleTxt']")
                self.driver.execute_script("""
                                   $(".packupButton").click(); 
                               """)
            elif "51taojinge.com" in self.driver.current_url or "html.1sapp.com" in self.driver.current_url:
                titleElement = self.driver.execute_script('return document.querySelector("h1")')
            elif "a.mp.uc.cn" in self.driver.current_url:
                titleElement = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'article-title')))
                self.driver.execute_script("""
                                           $(".show-all").click();
                                           $(".weixin").remove();
                                           $(".article-content").find("iframe").remove();
                                           Array.prototype.slice.call(document.querySelector(".article-content").querySelectorAll("img")).forEach(function(img){ img.src = img.attributes["data-original"].value})
                                       """)
            else:
                if "po.baidu.com/feed/error" in self.driver.current_url:
                    print("文章被禁，从links.txt中移除")
                    return "", ""
                titleElement = self.wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'h1')))
            self.driver.execute_script("""
                  (function(){
                  window.scroll(0,document.body.scrollHeight); 
                  })();
              """)
            contentElement = None
            if "baijiahao.baidu.com" in self.driver.current_url:
                contentElement = self.driver.find_element_by_xpath("//div[@id='content']")
            elif "mbd.baidu.com" in self.driver.current_url:
                contentElement = self.driver.execute_script('return $(".mainContent")[0]')
            elif "a.mp.uc.cn" in self.driver.current_url:
                contentElement = self.driver.find_element_by_xpath("//div[@class='article-content simple-ui']")
            elif "kuaibao.qq.com" in self.driver.current_url:
                contentElement = self.driver.find_element_by_xpath("//div[@class='content-box']")
            elif "toutiao.com" in self.driver.current_url:
                contentElement = self.driver.find_element_by_xpath("//div[@class='article-content']")
            elif "sohu.com" in self.driver.current_url:
                contentElement = self.driver.find_element_by_xpath("//article[@class='article']")
            elif "51taojinge.com" in self.driver.current_url or "html.1sapp.com" in self.driver.current_url:
                contentElement = self.driver.find_element_by_xpath("//div[@class='content']")
            content = self.driver.execute_script("return arguments[0].innerHTML", contentElement)
            content = content.replace(' src="//', ' src="http://')
            content = content.replace(' src="https//', ' src="http://')
            content = content.replace("&amp;", "&")
            content = content.replace("padding-top", "padding-top-x")
            return titleElement.text, content
        except:
            print("抓取异常")
            return "",""

    # 每个帐号每天的限额是6个，判断上传的资源是否超出6
    def canSubmit(self):
        result = self.driver.execute_script('return parseInt($(".z-red-font").text())')
        return result < 6

    # 退出登陆
    def logOut(self):
        logOutButton = self.wait.until(EC.element_to_be_clickable((By.ID, 'logout')))
        #logOutButton = self.driver.find_element_by_id("logout")
        logOutButton.click()
        print("退出登陆")
        sleep(1)
        self.downloadArticleOrNot()

    # 点击发布MENU
    def clickDeliveryMenu(self):
        articleMenu = self.wait.until(EC.element_to_be_clickable((By.XPATH, '(//li[@class="menu-item"])[2]')))
        articleMenu.click()

    # 保存文章
    def doFormSubmit(self,article, account):
        sleep(random.choice([2, 4, 6]))
        title, content =  article["title"], article["content"]
        if article["url"] in self.articleTitleDic.keys():
            title = self.articleTitleDic[article["url"]]
        self.clickDeliveryMenu()

        if self.canSubmit() == False:
            return False

        sleep(2)
        titleElement = self.driver.find_element_by_id("title")
        titleElement.clear()
        if len(title) > 27:
            title = title[0:27]
        while len(title) < 12:
            title = title + "一"
        titleElement.send_keys(title)
        editorElement = self.driver.find_element_by_id("container")
        editorElement.clear()
        # editorElement.send_keys(content)
        content = content.replace("\n", "")
        self.driver.execute_script("arguments[0].innerHTML = '" + content + "'", editorElement)
        dropDownToggle = self.driver.find_element_by_class_name("dropdown-toggle")
        dropDownToggle.click()
        categoryName = '<span class="text">' + getConfigByKey("文章分类") + '</span>'
        categoryAnchor = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-normalized-text='" + categoryName + "']")))
        categoryAnchor.click()

        self.driver.find_element_by_xpath("//a[@href='#auto']").click()
        sleep(random.randrange(5, 10))
        #self.driver.find_element_by_xpath("//div[@class='cover-img']").click()

        self.driver.find_element_by_class_name("js_article_submit").click()
        sleep(random.randrange(1, 2))
        btnOk = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'js-btn-ok')))
        result = self.driver.execute_script('return $(".modal-body").text()')
        print("帐号：" + account + " 标题：" + title + " 处理结果：" + result)
        btnOk.click()
        if result.__contains__("已经发布过"):

            removeLinkLine(article["url"])
            print("发布失败：" + result)
            sleep(1)
            self.driver.execute_script("""
                   (function(){
                   window.scroll(0,0); 
                   })();
               """)
            self.driver.refresh()
            self.driver.switch_to.alert.accept()
            anchorCancel = self.driver.find_element_by_xpath("//a[text()='取消']")
            self.jsClick(anchorCancel)
            self.driver.find_element_by_xpath("//a[contains(text(),'内容管理')]").click()
        else:
            removeLinkLine(article["url"])
            print("发布成功，从links.txt文件中移除链接"+article["url"])

        return True

    # 提交视频
    def submitVideoForm(self,video):
        filePath = video["url"]
        try:
            self.clickDeliveryMenu()
        except:
            self.driver.refresh()
            self.submitVideoForm(filePath)

        if self.canSubmit() == False:
            return False

        tabs = self.driver.find_elements_by_class_name("tab")
        tabs[2].click()
        sleep(1)
        nameWithExtendsion = os.path.basename(filePath)
        nameWithExtendsion = nameWithExtendsion.split(".")[0]
        if len(nameWithExtendsion) < 11 or len(nameWithExtendsion) > 27:
            print("invalid path name")
            return False
        titleElement = self.driver.find_element_by_id("video-up-input")
        titleElement.send_keys(filePath)
        keywords = dividewords(nameWithExtendsion,video["category"])
        sleep(1)
        tagsInput = self.driver.find_element_by_id("form-tags-input")
        descriptionInput = self.driver.find_element_by_id("description")
        for keyword in keywords:
            tagsInput.clear()
            tagsInput.send_keys(keyword)
            descriptionInput.clear()
            sleep(1)

        # 选择视频分类为娱乐
        self.driver.find_element_by_xpath("//button[@data-id='c-first']").click()

        categoryName = '<span class="text">' + video["category"] + '</span>'
        categoryAnchor = self.driver.find_element_by_xpath("//a[@data-normalized-text='" + categoryName + "']");
        categoryAnchor.click()
        # 默认选择自动
        self.driver.find_element_by_xpath("//label[@for='cover1']").click()
        # 选择封面
        sleep(3)
        cover = self.driver.find_element_by_class_name("pic-cut")
        coverList = cover.find_elements_by_tag_name("li")

        #有可能视频传得慢，所以这里要等
        retryCount = 20
        while len(coverList) <=0 and retryCount>0:
            sleep(2)
            coverList = cover.find_elements_by_tag_name("li")
            retryCount = retryCount -1

        if len(coverList) <=0:
            print("上传失败，有可能是视频上传较慢导致，请检查网络是否畅通，视频大小是否正常")
            return False
        else:
            coverList[0].click()
        # 提交表单
        sleep(1)
        self.driver.find_element_by_xpath("//button[@type='submit']").click()
        btnOk = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'js-btn-ok')))
        result = self.driver.execute_script('return $(".modal-body").text()')
        print( " 视频文件：" + filePath + " 处理结果：" + result)
        btnOk.click()
        moveFile(video["url"])
        print("将"+video["url"]+"移动到handled文件夹中")
        return True

try:
    robot = NetbaseRobot()
    robot.login(0)
except Exception as e :
    print(e)