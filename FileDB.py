import os
import sys
import PySimpleGUI as sg
import numpy as np
import DB
from collections import Counter
import hashlib
from pprint import pprint

sep = os.sep
keys = ['False', 'await', 'else', 'import', 'pass', 'None', 'break', 'except', 'in', 'raise', 'True', 'class', 'finally', 'is', 'return', 'and', 'continue', 'for', 'lambda', 'try', 'as', 'def', 'from', 'nonlocal', 'while', 'assert', 'del', 'global', 'not', 'with', 'async', 'elif', 'if', 'or', 'yield']

def flatten(lst):
    return list(np.array(lst).flatten())
    
def most_common(lst, n=None):
    lst1 = list(Counter(lst).most_common(n))
    lst2 = []
    for s, n in lst1:
        n1 = len(s)
        if n1 < 4 or n1 > 64 or s in keys:
            continue
        lst2.append(s)        
    return lst2
    
def last_common(lst, n=None):
    lst1 = list(Counter(lst).most_common(n))
    lst2 = []
    for s, n in lst1:
        n1 = len(s)
        if n1 < 4 or n1 > 64 or s in keys:
            continue
        lst2.insert(0, s)        
    return lst2
    
def common_word(lst):
    s = str(lst)
    wlst = re.findall('[a-zA-Z][\w\_\-]*', s)
    return most_common(wlst)
    
def dct2data(dct):
    headers = list(dct.keys())
    data = []
    n1 = len(headers)
    items = list(dct.values())
    n2 = len(items[0])    
    for i in range(n2):
        p = [items[j][i] for j in range(n1)]
        data.append(p)
    return data, headers, n1
      

class FileDB():    
    def __init__(self):
        self.db = self.conn = DB.open('file')
        self.tables = self.db.get_table_names()
        self.hash = hashlib.blake2b(digest_size=4)
        self.cache = self.db.get('cache')
        self.dirmap = eval(self.cache.get('dirmap'))
        self.homepath = self.dirmap.get('~')
        
    def reset(self):
        self.create_tables() 
        lst = []
        for path in pdct:
            path = get_path(path)
            if not path in lst:
                lst.append(path)
        for path in lst:
            self.cache_dir(path)
            
    def hash_key(self, s):
        res = self.get('word', s)
        if res != '[]':
            return res
        m = self.hash
        data = s.encode()    
        m.update(data)
        hcode = m.hexdigest()
        self.set('cache', hcode, s)
        self.set('word', s, hcode)
        return hcode
        
    def keys(self, table):
        return self.db.fetchall('Select name from %s' % table)
        
    def create_tables(self, tables=['dir', 'files', 'text', 'cache', 'word']):
        for table in tables:
            self.db.create(table)          
       
    def cache_dir(self, name):
        path = get_path(name)
        dirs = get_dirs(path)
        self.set('dir', name, str(dirs))
        self.set('dir', path, str(dirs))
        
    def cache_files(self, name, ext='.py'):
        path = get_path(name)
        files = get_files(path, ext)
        self.set('files', path, str(files))
        #for fn in files:     
        #    self.cache_file_text(name, path, fn)       
        
    def cache_file_text(self, path, filename):   
        filepath = path + os.sep + filename
        path, filename = filepath.rsplit(os.sep, 1)
        hcode = self.hash_key(path) 
        print(hcode + os.sep + filename, filepath)        
        
        text = fread(filepath)        
        lst0 = re.findall('[a-zA-Z][\w\_\-]+', text)
        lst1 = last_common(lst0)
        self.set('text', hcode + os.sep + filename, ','.join(lst1))        
        
    def get_dir(self, name):
        path = get_path(name)
        return self.get('dir', name)
        
    def get_files(self, name):
        return eval(self.get('files', name))
        
    def search(self, table, key):
        return self.db.execute(f'SELECT * FROM {table} WHERE data LIKE \'%{key}%\';')        
    
    def map_path(self, fn):
        key, name = fn.split(sep, 1)
        path = self.cache.getdata(key)
        ch = path[0]
        if ch == '~':
           path = path.replace('~', self.homepath)
        elif ch == '#':
            p0, p1 = path.split(sep, 1)
            path = self.dirmap.get(p0) + sep + p1
        return path + sep + name   
                
    def find_text(self, key):
        res = self.db.fetchall(f'SELECT name FROM text WHERE data LIKE \'%{key}%\';', flat=True)
        sep = os.sep
        lst = []
        for fn in res:            
            path = self.map_path(fn)
            lst.append(path)
        return lst
        
    def fetchall(self, table):
        return self.db.fetchall('SELECT * FROM %s' % table)          
       
    def set(self, table, key, data):        
        self.db.execute(f'DELETE FROM {table} WHERE name = \"{key}\";')     
        data = str(data)
        s1 = f"INSERT INTO {table} (name, data) VALUES "
        s2 = "(\"%s\", \"%s\") ;" % (key, data)
        #s3 = " ON DUPLICATE name UPDATE value = \"%s\";" % (value)
        self.db.execute(s1 + s2 ) 
        self.db.commit()    
        
    def get(self, table, key):
        lst = self.db.fetchall(f"SELECT data FROM {table} where name=\"{key}\"")
        if lst == [] or lst == None:
            return str(lst)
        return str(flatten(lst)[0])          
        
    def show(self):
        self.db.show()
    
def cache_files(db):
    for d in ['src', 'p1', 'p2', 'p5', 'test']:
        path = get_path(d)
        print(path)
        #db.cache_files(d)
        files = db.get_files(path)
        for fn in files:     
            db.cache_file_text(path, fn)   
            sys.stdout.flush()

def create_dirmap():
    sdb = FileDB().db 
    sdb.remove_table('dirmap')
    table = sdb.get('cache')
    
    lst = [('/usr/lib/python3/dist-packages', '#dist'),
           ('/usr/lib/python3.8', '#sys'),
           ('/home/athena/.local/lib/python3.8/site-packages', '#local'), 
           ('/home/athena', '~')]
    dct = {}
    for a, b in lst:
        dct[a] = b
        dct[b] = a
    table.setdata('dirmap', str(dct))
    pprint(table.get('dirmap'))
    
def temp(db):
    db.create_tables()
    for d in ['src', 'p1', 'p2', 'p5', 'test']:
       db.cache_dir(d)
    cache_files(db)
    
def test_search(key):
    db = FileDB()
    res = db.find_text(key)
    pprint(res)

if __name__ == '__main__':
    db = FileDB() 
    db.show()



  


