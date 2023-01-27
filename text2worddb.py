import os
from fileio import *
from DB import CacheDB
import jieba        
cdb = CacheDB()
path = cdb.get('a-note.path') + os.sep
print(path)

word_dct = {}

def add_word(word):
    n = word_dct.get(word, 0)
    word_dct[word] = n + 1
    
def text2words(text):
    lines = text.splitlines()
    lst = []
    for line in lines:
        seg_list = jieba.cut(line, cut_all=False)
        for word in seg_list:
            add_word(word)
    
def pushall():        
    for fn in os.listdir(path):
        if '.txt' in fn:
            print(fn)
            text = fread(path + fn)
            #print(text[0:100])
            text2words(text)
    for key, value in word_dct.items():    
        cdb.setword(key, value)         

def getwords():
    res = cdb.getwords()
    print(res)
    

getwords()

