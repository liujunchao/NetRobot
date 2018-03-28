import os,sys
import shutil

def eachFile(filepath):
    pathDir =  os.listdir(filepath)
    files = []
    for allDir in pathDir:

        child = os.path.join('%s%s' % (filepath, allDir))
        childDir  = os.listdir(child)
        for childFile in childDir:
            if len(childFile) <6:
                continue

            if childFile.endswith(".mp4") and len(childFile)>=15 and len(childFile)<=31:
                dic = {}
                dic["url"] = os.path.join('%s%s/%s' % (filepath,allDir, childFile))
                dic["category"] = allDir
                files.append(dic)
    return files



def cur_file_dir():
    # 获取脚本路径
    path = sys.path[0]
    # 判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)

def getVideoFiles():
    currentPath = cur_file_dir()
    currentPath = currentPath.replace("/src","")+"/video/"
    return eachFile(currentPath)

def getVideoHandledPath():
    currentPath = cur_file_dir()
    return currentPath+ "/handled/"

def moveFile(srcPath):
    try:
        dest = getVideoHandledPath()
        shutil.move(srcPath, dest)
    except Exception as err:
        print(err)



def getAccounts():
    accounts = open('account.txt').read()
    accountList = []
    for account in accounts.split("\n"):
        account =account.strip()
        if account == "":
            continue
        accountpw = account.split(" ")
        list =[]
        for itm in accountpw:
            if itm == "":
                continue
            list.append(itm)
        accountList.append(list)
    return accountList

def getConfig():
    config = {}
    configFile = open('config.txt', encoding='utf-8').read()
    for configItm in configFile.split("\n"):
        arr = configItm.split("=")
    return config

def getMarksList(markList):
    marks = markList.split(" ")
    list = []
    for itm in marks:
        if itm == "":
            continue
        list.append(itm)
    return list

userConfig = []

def getConfigByKey(key):
    if len(userConfig)==0:
        configFile = open('config.txt', encoding='utf-8').read()
        for configItm in configFile.split("\n"):
            configItm = configItm.strip()
            if configItm == "":
                continue
            arr = configItm.split("=")
            marks = getMarksList(arr[1])
            userConfig.append({
                "name":configItm,
                "value":marks
            })
    for cfg in userConfig:
        if key in cfg["name"] and "文章分类" in cfg["name"]:
            return cfg["value"][0]
        if key in cfg["name"]:
            return cfg["value"]
    return []

def removeLinkLine(rmLine):
    f = open("links.txt", "r",encoding='utf-8')
    lines = f.readlines()
    f.close()
    f = open("links.txt", "w",encoding='utf-8')
    for line in lines:
        if rmLine not in line:
            f.write(line)
    f.close()

def removeAccountLine(account,pw):
    f = open("account.txt", "r")
    lines = f.readlines()
    f.close()
    f = open("account.txt", "w")
    for line in lines:
        if account not in line or pw not in line:
            f.write(line)

    f.close()

def convertList(line):
    arr  = []
    line = line.replace("\t"," ")
    for content in line.split(" "):
        if content!='':
            arr.append(content)
    return  arr

obj = getVideoFiles()
# print(obj)
# src = obj[0]["健康"][0]
# removeLinkLine("https://stackoverflow.com/questions/45528729/is-there-a-better-way-for-deleting-a-line-from-file-in-python-i-alraedy-have-a?noredirect=1&lq=1")