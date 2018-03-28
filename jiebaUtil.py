import jieba
import jieba.posseg as pseg
from fileUtil import getConfigByKey

def dividewords(desc,category):
    words = pseg.cut(desc)
    rlt = []
    for w in words:
        if w.flag == "n" or w.flag == "ns"or w.flag == "nr":
            rlt.append(w.word)
    idx = 1

    if len(rlt)<3:
        rlt = getConfigByKey(category+"标签")
    while len(rlt)<3:
        rlt.append("标签"+str(idx))
        idx = idx +1
    return rlt