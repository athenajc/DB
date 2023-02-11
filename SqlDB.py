import os
import re
import sqlite3

import numpy as np
import json
from collections import Counter
from pprint import pprint, pformat

p1 = '/usr/lib/python3.8'           
p2 = '/link/localpack'
p3 = '/link/src'
p4 = '/link/test'
p5 = '/link/distpack'
pdct ={'usr':p1, 'local':p2, 'src':p3, 'test':p4, 'tmp':'~/tmp', 'p1':p1, 'p2':p2, 'p5':p5, 'dist':p5,
       'db':'~/data', 'icon':'~/data/icon', 'gallery':'~/data/gallery'}
       

pykeys = ['FALSE', 'await', 'else', 'import', 'pass', 'None', 'break', 'except', 'in', 'raise', 'TRUE', 'class', 'finally', 'is', 'return', 'and', 'continue', 'for', 'lambda', 'try', 'as', 'def', 'from', 'nonlocal', 'while', 'assert', 'del', 'global', 'not', 'with', 'async', 'elif', 'if', 'or', 'yield']

    
def realpath(path):
    if '~' in path:
        path = os.path.expanduser(path)            
    path = os.path.realpath(path) 
    return path
    
def _get_path(name):
    path = pdct.get(name, name)
    return realpath(path) 
    
def flatten(lst):
    return list(np.array(lst).flatten())
    
def flatstr(lst):
    lst = list(np.array(lst).flatten())
    return ','.join(lst)
    
def most_common(lst, n=None):
    lst1 = list(Counter(lst).most_common(n))
    lst2 = []
    for s, n in lst1:
        lst2.append(s)        
    return lst2
    
def last_common(lst, n=None):
    lst1 = list(Counter(lst).most_common(n))
    lst2 = []
    for s, n in lst1:
        lst2.insert(0, s)        
    return lst2
    
def common_word(lst):
    s = str(lst)
    wlst = re.findall('[a-zA-Z][\w\_\-]*', s)
    return most_common(wlst)
    
def cmd2dct(cmd):
    dct = {}
    a = cmd.index('(')
    b = cmd.index(')')
    cmd = cmd[a+1:b]
    for p in cmd.split(','):    
        p = p.strip()
        if p == '':
            continue

        if '\t' in p:
            a, b = p.split('\t')
            a = a.replace('\"', '')
        else:
            a, b = p.split(' ')    
        dct[a] = b
    return dct  
    
def info2dct(info):
    dct = {}
    for p in info:
        if p[0] == 'table':            
            a, name, b, n, cmd = p
            d = {}
            d['column'] = cmd2dct(cmd)
            d['count'] = n
            dct[name] = d            
    return dct
        
            
class Table():
    def __init__(self, db, name):      
        self.db = db
        self.name = name        
        self.key = 'name'
        self.execute = self.db.execute
        self.commit = self.db.commit
        self.executemany = self.db.executemany

    def show(self):
        from DB.dbView import dbTableView
        dbTableView(self).show()
        
    def get_info(self):
        return self.db.get_table_info(self.name)
        
    def get_columns(self):
        return self.db.get_columns(self.name)

    def remove(self):        
        self.db.remove_table(self.name)
        
    def clear(self):
        self.execute(f'DELETE FROM {self.name};')   
        self.commit()
        
    def set_list(self, lst):
        self.clear()
        self.add_list(lst)
    
    def add_list(self, lst):     
        if lst == None or lst == []:
            return   
        s = '?,'*len(lst[0])
        fields = s[0:-1]
        self.executemany(f"INSERT INTO {self.name} VALUES ({fields})", lst)   
        
    def add_dict(self, dct):     
        if dct == None or dct == {}:
            return   
        fields = '?, ?'
        lst = []
        for k, v in dct.items():
            lst.append((str(k), str(v)))
        self.executemany("INSERT INTO %s VALUES(%s)" % (self.name, fields), lst)       
        
    def delete_key(self, key):        
        self.db.execute(f'DELETE FROM {self.name} WHERE name = \"{key}\";')   
        self.commit()
        
    def insert_data(self, key, data): 
        self.db.insert_data(self.name, key, data)
        
    def adddata(self, key, data):        
        self.insert_data(key, data) 
        
    def deldata(self, key):
        self.db.execute(f'DELETE FROM {self.name} WHERE name = \"{key}\";')   
        self.commit()
        
    def setdata(self, key, data):        
        self.db.execute(f'DELETE FROM {self.name} WHERE name = \"{key}\";')   
        self.db.insert_data(self.name, key, data)
        
    def getdata(self, key=None, default=None):
        if key == None:
            return self.getall()
        res = self.db.fetchone(f"SELECT data FROM {self.name} WHERE name=\"{key}\"")    
        if res == None and default != None:
            return default
        return res
        
    def renamedata(self, key, newkey):
        data = self.getdata(key)
        self.delete_key(key)
        self.insert_data(newkey, data) 
        
    def search(self, key):
        res = self.getdata(key)
        if res != None and len(res) > 0:
            return res
        res = self.db.fetchall(f'SELECT name FROM {self.name} WHERE name LIKE \'%{key}%\';', flat=True)        
        return res
        
    def getnames(self):
        return self.db.fetchall(f'select name from {self.name}', flat=True)  
        
    def getkeys(self, key=None):
        if key == None:
            return tuple(self.get_columns().keys())
        return self.db.fetchall(f'select {key} from {self.name}', flat=True)  
        
    def getall(self):
        return self.db.fetchall(f'select * from {self.name}', flat=False)          
        
    def get(self, key='keys'):
        if key == '*':
            return self.getall()
        elif key in ['names', 'keys']:
            return self.getnames()     
        else:
            return self.search(key)    
            
    def print(self, key='all'):
        if key == 'all':
            res = self.getall()
        else:
            res = self.get(key)
        pprint(res)
        

class SqlDB(object):
    def __init__(self, filename=None):   
        self.dct = {}    
        self.tables = None
        self.table = None
        self.print = pprint
        self.name = filename
        if len(filename) == 0:
            self.db = self.conn = None
        else:
            self.db = self.conn = self.connect(filename)
        self.tables = self.get_table_names() 
        self.logs = []        
                
    def get(self, table='tables'):
        if table == 'tables':
            return self.get_table_names()
        return self.get_table(table)
        
    def log_error(self, e):
        print('Error', e)
        self.logs.append(('Error', e))
        
    def connect(self, filename):
        if not '.db' in filename:
            filename = realpath(f'~/data/{filename}.db')
        else:
            filename = realpath(filename)
        if not os.path.exists(filename): 
            return None            
        self.filename = filename
        conn = None
        try:
            conn = sqlite3.connect(filename)
            return conn
        except sqlite3.Error as e:
            print('Error:SqlDB connect : ', filename)
            self.log_error(e)    
        self.db = self.conn = conn    
        return conn
        
    def close(self):
        self.db.close()
        
    def commit(self):
        try:
            self.db.commit()    
        except sqlite3.Error as e:
            self.log_error(e)     
        
    def cursor(self):
        return self.db.cursor()
        
    def execute(self, cmd, data=None):
        if self.db == None:
            return
        try:
             cursor = self.db.cursor()
             if data != None:
                 res = cursor.execute(cmd, data)
             else:    
                 res = cursor.execute(cmd)   
             return res
        except sqlite3.Error as e:
             self.log_error(e)
        return     
        
    def fetchall(self, cmd, flat=False):
        res = self.execute(cmd)  
        if res == None:
            return []
        lst = res.fetchall()
        if flat == True:
            return flatten(lst)
        return lst
        
    def fetchone(self, cmd):
        res = self.execute(cmd)  
        if res == None:
            return 
        res = res.fetchone()
        if res == None or res == ():
            return 
        return res[0]    
             
    def executemany(self, cmd, data):
        if self.db == None:
            return        
        try:
            self.db.cursor().executemany(cmd, data)
            self.db.commit()   
        except sqlite3.Error as e:
             self.log_error(e)     
             
    def remove_table(self, name):        
        cmd = "DROP table IF EXISTS %s" % name
        self.execute(cmd)
        self.commit()
        return self.update_index()
        
    def get_table(self, name):
        if name in self.dct:
            return self.dct[name]
        tables = self.get_table_names()
        if name in tables:
            self.dct[name] = table = Table(self, name)
            return table
        else:
            print('Table', name, 'not exists')
            print('table names', self.get_table_names())
            return None   
        
    def create(self, name, cmd=None):
        if cmd == None:
            cmd = f"CREATE TABLE IF NOT EXISTS {name} (name string, data string)"
        self.execute(cmd)
        self.commit() 
        
        self.update_index()
        return self.get_table(name)
        
    def create_table(self, name, dct=None, cmd=None):   
        head = f"CREATE TABLE  IF NOT EXISTS {name} "
        if cmd != None:
            return self.create(name, head + str(cmd))
        lst = []
        for key, datatype in dct.items():
            lst.append('%s %s' % (key, datatype))
        cmd = '(%s)' % ','.join(lst)
        return self.create(name, head + cmd)
        
    def table_fetchall(self, table):
        res = self.fetchall(f"SELECT * FROM {table}")
        return res
        
    def update_index(self):
        self.tables = None
        tables = self.get_table_names()
        index = 'cache'
        if not index in tables:
            self.create(index)
            return
        
        res = self.fetchall("SELECT * FROM sqlite_master;")  
        dct = info2dct(res)
        table = self.get_table(index)        
        table.setdata('SQL.INDEX', str(dct))     
        return dct    
        
    def get_table_names(self):
        if self.tables == None:            
            # select all the tables from the database
            self.tables = self.fetchall("SELECT name FROM sqlite_master WHERE type='table';", flat=True)      
        return self.tables
        
    def get_info(self):
        res = self.getdata('cache', 'SQL.INDEX')
        if len(res) == 0:
            return self.update_index()
        else:
            return eval(res)    
        #res = self.fetchall("SELECT * FROM sqlite_master;")   
        #return res
        
    def get_table_info(self, table='*'):
        if table == '*':
            return self.get_info()
        dct = self.get_info()
        return dct.get(table)
        
        #res = self.fetchone(f"SELECT * FROM sqlite_master where name=\"{table}\";" )   
        #return res
        
    def get_columns(self, table):
        res = self.get_table_info(table)
        if res == None or type(res) != dict:
            return
        return res.get('column')
        
    def dataframe_keytypes(self, dataframe):
        lst = []
        for a, b in dataframe.dtypes.items():
            lst.append(str(a) + ' ' + str(b))        
        return ','.join(lst)        
    
    def add_list(self, table, lst):     
        if lst == None or lst == []:
            return   
        n = len(lst[0])
        fields = ', '.join(["?"]*n) 
        self.executemany("INSERT INTO %s VALUES(%s)" % (table, fields), lst)   
        
    def add_dict(self, table, dct):     
        if dct == None or dct == {}:
            return   
        fields = '?, ?'
        lst = []
        for k, v in dct.items():
            lst.append((str(k), str(v)))
        self.executemany("INSERT INTO %s VALUES(%s)" % (table, fields), lst) 

    def from_dict(self, table, dct):
        self.create_table(table, dct={'name':'string', 'data':'string'})         
        self.add_dict(table, dct)
        
    def from_list(self, table, keytypes, lst):
        self.create_table(table, dct=keytypes)          
        self.add_list(table, lst)     
                        
    def query(self, table, item, key, value):
        res = self.execute("SELECT %s FROM %s where %s=\"%s\"" % (item, table, key, value))
        return res        
                
    def delete_key(self, table, key):        
        self.execute(f'DELETE FROM {table} WHERE name = \"{key}\";')   
        self.commit()
        
    def insert_data(self, table, key, data): 
        data = str(data)
        cmd = f"INSERT INTO {table} (name, data) VALUES (?,?)"
        self.execute(cmd, (key, data)) 
        self.commit()    
        
    def adddata(self, table, key, data):        
        self.insert_data(table, key, data) 
        
    def setdata(self, table, key, data):        
        self.execute(f'DELETE FROM {table} WHERE name = \"{key}\";')     
        self.insert_data(table, key, data) 
        
    def getdata(self, table, key):
        lst = self.fetchall(f"SELECT data FROM {table} WHERE name=\"{key}\"")
        if lst == [] or lst == None:
            return str(lst)
        return str(flatten(lst)[0])     
        
    def get_cache(self, key):
        return self.getdata('cache', key)
        
    def set_cache(self, key, data):
        self.setdata('cache', key, data)
        
    def renamedata(self, table, key, newkey):
        data = self.getdata(table, key)
        self.delete_key(table, key)
        self.insert_data(table, newkey, data) 
        
    def search(key, table='cache'):
        res = self.fetchall(f'SELECT name FROM {table} WHERE name LIKE \'%{key}%\';', flat=True)        
        return res
        
    def getnames(self, table):
        return self.fetchall(f'select name from {table}', flat=True)   
        
    def select(self, table):
        self.table = table
        
    def show(self):
        from DB.dbView import dbView
        dbView(self).show()

dbs = {}


def open(file):
    if not file in dbs:
        dbs[file] = SqlDB(file)
    return dbs.get(file)    

def get_table(file, table):
    sdb = open(file)
    return sdb.get_table(table)
    
def getdata(file, table, key='keys'):
    sdb = open(file)
    return sdb.get_table(table).get(key)
    
def get(key):
    if len(key) == 0:
        return open('cache')
    if key in ['file', 'cache', 'code', 'modules']:
        return open(key)

    if '.' in key:        
        p = list(key.split('.', 3))
        db = open(p.pop(0))
        table = db.get_table(p.pop(0))
        if p == []:
            return table
        return table.get(p[0])
            
    if key in globals():
        return globals().get(key)  
    db = open('cache')
    res = db.getdata('cache', key)        
    return res
     
def get_cache(key):
    db = open('cache')    
    data = db.getdata('cache', key)
    return data
    
def set_cache(key, data):
    db = open('cache')
    db.setdata('cache', key, data)
    
getcache = get_cache
setcache = set_cache
    
def search(key, fn = 'cache', table='cache'):
    db = open(fn)
    res = db.fetchall(f'SELECT name FROM {table} WHERE name LIKE \'%{key}%\';', flat=True)
    return res
    
def getnames(fn, table=None):
    db = open(fn)
    if table == None:
        return db.get_table_names()
    return db.get_table(table).getnames()

    
def is_code(text):
    if not '\n' in text:
        return False
    n = 0
    if 'def ' in text or 'class ' in text:
        n += 2
    for key in pykeys:
        if key in text:
            n += 1
            if n >= 3:
                return True
    return False  


def show(fn, table):
    table = get_table(fn, table)
    if table != None:
       table.show()        

def get_path(name):
    table = get_table('cache', 'path')
    path = table.getdata(name)
    return path
    
def cache_path(name, value):
    table = get_table('cache', 'path')
    table.setdata(name, value)
    return table

def puts(data):        
    pprint(data)        
    
        
#def test_info():
#    sdb = open('cache')
#    sdb.update_index()
#    print(sdb.get_info())
    #table = db.get('link')
    #table.show()
    #db.remove_table('word')
    #datalst = table.getdata()
                
def db_show(name='code'):
    db = open(name)
    db.show()
    
if __name__ == '__main__':
    path = get_path('src')
    print(path)



    
           





