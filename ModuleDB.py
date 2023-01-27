import os
import re
import sys
import pydoc
import pathlib
import inspect
import pkgutil
import importlib 
from fileio import *
from DB import SqlDB
import numpy as np
import pandas
import zlib
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from pprint import pprint

objdct = {}   

def get_modules():
    db = SqlDB('~/data/modules.db')
    modules = db.fetchall("SELECT name FROM module_file", flat=True) 
    db.close()
    return modules
    
modules = get_modules()

def get_obj(thing):
    global objdct
    if type(thing) != str:
        return thing

    if thing in objdct:
        return objdct.get(thing)
    try:   
        #obj = pydoc.locate(thing) 
        obj, name = pydoc.resolve(thing)
        objdct[thing] = obj
    except Exception as e:
        print('resolve Error', thing, str(e))
        return None    
    return obj
        
def grep(path, pattern):
    for fn in os.listdir(path):
        with open(fn, "r") as file:
            for line in file:
                if re.search(pattern, line):
                     return fn, line
    return None, ''                 
   
            
class ModuleObj(object):
    def __init__(self, name):
        self.name = name
        self.module = None
        self.obj = obj = get_obj(name) 
        self.dct = {}       
        #self.dct = self.init_attr(obj)
        self.members = None
        self.doc = None 
        
    def get_attr(self, key):
        if self.obj == None:
            return None
        #print(self.name, key)    
        if hasattr(self.obj, key) == False:
            return None
        try:
            return self.obj.__getattribute__(key)
        except:            
            return None
            
    def get_type(self):
        if self.obj == None:
            return None
        return type(self.obj)
            
    def check_isbuiltin(self):
        if self.name in os.__builtins__:
            return True
        return False
        
    def get_spec(self):
        spec = self.get_attr('__spec__')    
        if spec == None or spec == 'none':
            return ''    
        if hasattr(spec, '__dict__'):
            return spec.__dict__
        return spec

    def get_doc(self, n=None):
        doc = self.get_attr('__doc__')
        if n == None:
            return doc
        n1 = doc.count('\n')
        if n1 < n:
            return doc
        lst = doc.splitlines()[0:n]
        return '\n'.join(lst)                
            
    def init_attr(self, obj):
        dct = {}
        lst = ['file', 'package', 'docformat', 'spec', 'version']  #'all'
        for k in lst:
            v = self.get_attr('__%s__' % k)            
            if v == None:
                v = ''
            dct[k] = v 
            self.__setattr__(k, v)                
        return dct       
        
    def get_module(self):
        if self.obj == None:
            return ''
        if self.module != None:
            return self.module
        obj = self.obj    
        for s in ['__module__', '__package__']:
            if hasattr(obj, s):   
               return getattr(obj, s)
        self.module = inspect.getmodule(obj)    
        return self.module
        
    def get_module_members(self):
        #self.msg.puts('get_module_members', objname)     
        dct = {'module':[], 'class':[], 'function':[]} 
        if self.obj == None:
            return dct
        
        try:
            for name, des in inspect.getmembers(self.obj):
                for item in dct:
                    if str(des).find(item) == 1:                    
                        dct[item].append(name)
        except:
            print('get_module_members error')        
        return dct   
        
    def get_members(self, key='dct'):   
        if self.members == None or self.members == {}:
           self.members = dct = self.get_module_members()   
        else:
           dct = self.members
        
        if key == 'dct':
           return dct    
        elif key == 'all':      
           return dct['module'] + dct['class'] + dct['function']      
        elif key in ['module', 'class', 'function']:
           return dct.get(key, [])               
        return dct.get(key, [])
    
class ModuleUtils():    
    def __init__(self):        
        self.dct = {}
        self.modules = modules
        
    def get_modules(self):
        #if self.modules == None:            
        #   self.modules = get_lst('modules')
        return self.modules
        
    def get_obj(self, name):
        if name in self.dct:
            return self.dct[name]
        obj = ModuleObj(name) 
        self.dct[name] = obj
        return obj     
        
    def get_module_file_list(self):
        lst = []
        for s in self.get_modules():
            obj = self.get_obj(s)
            info = (obj.name, obj.file)         
            lst.append(info)
        return lst
        
    def get_function_list(self, modules):
        from get_functions import get_obj_funcs
        lst1 = []        
        for objname in modules:
            lst = []    
            get_obj_funcs(objname, lst, modules, 0)    
            lst1 += lst
        lst = list(set(lst1))
        lst.sort()    
        return lst
                
class ModuleDB(ModuleUtils):
    db = conn = SqlDB('~/data/modules.db')
    tables = db.get_table_names()    
    
    def __init__(self):    
        ModuleUtils.__init__(self)    
        self.dct = {}    
        self.modules = self.fetch_modules()  
        
    def fetch(self, cmd, flat=False):
        return self.db.fetchall(cmd, flat) 
        
    def fetch_modules(self, flat=False):    
        return self.db.fetchall("SELECT name FROM module_file", flat=flat)         
        
    def fetchall(self, table, key='*', flat=False):    
        return self.db.fetchall("SELECT %s FROM %s" % (key, table), flat=flat) 
        
    def fetch_filelist(self):    
        return self.db.fetchall("SELECT * FROM module_file") 
        
    def gen_module_file(self):
        lst = self.get_module_file_list()
        keytypes = {'name':'string', 'file':'string'} 
        self.db.from_list('module_file', keytypes, lst)
      
    def gen_function_list(self, modules=None):
        if modules == None:
            modules = self.get_modules()
        lst = self.get_function_list(modules)
        keytypes = {'path':'string', 'name':'string', 'module':'string'} 
        self.db.from_list('function_list', keytypes, lst)
              
    def gen_table(self, table): 
        if table == 'module_file':
            self.gen_module_file()
        elif table == 'function_list':
            self.gen_function_list()      
        self.close_db()
        
    def search_module(self, key, flat=False):  
        res = self.db.execute("SELECT name FROM module_file where name like ?", ('%'+key+'%',)) 
        lst = res.fetchall()
        if flat == True:
            lst = flatten(lst)
        return lst
        
    def search_function(self, key, pathkey=None, flat=False):   
        res = self.db.execute("SELECT path FROM function_list where path like ?", ('%'+key+'%',)) 
        lst = res.fetchall()
        if flat == True:
            lst = flatten(lst)
        return lst
        
    def search(self, key):
        lst = self.search_module(key, flat=True)
        res = self.search_function(key, flat=True)
        return lst + res
        
    def get_modules(self):
        lst = self.fetchall('module_file', 'name')
        return flatten(lst)
        
    def flat(lst):
        return list(np.array(lst).flatten())
        
    def flatstr(lst):
        lst = list(np.array(lst).flatten())
        return ','.join(lst)
        
    def setvar(self, key, value):    
        self.db.setdata('cache', key, value)
        
    def getvar(self, key):
        return self.db.getdata('cache', key)
        

    
def flatten(lst):
    return list(np.array(lst).flatten())
    
def flatstr(lst):
    lst = list(np.array(lst).flatten())
    return ','.join(lst)
    
class test():        
    def test_search():
        lst = search_func_from_db('tag%', 'tki%')
        lst = filter_prefix(lst, 'werk')
        pprint(lst)
        
    def get_modules():
        return test.db.get_modules()
        
    def gen_tables():
        #db.gen_table('module_file')
        #db.gen_table('function_list')
        pass
        
    def search(key):
        lst = test.db.search_module(key, flat=True)
        #pprint(lst)
        res = test.db.search_function(key, flat=True)
        #pprint(res)
        return lst + res
        
    def filter():
        lst = test.search_obj('%search%') 
        lst = flatten(lst)
        data = ModuleDB.flat(lst)
        r = re.compile("t.*")
        filtered_list = list(filter(r.match, lst))
        #print(filtered_list)
        
    def create_cache_table():
        db = ModuleDB().db 
        dct = {'key':'values', 'values':'test'}
        db.from_dict('cache', dct)
        
mdb = ModuleDB() 
class HelpObj(ModuleObj):
    def __init__(self, name):
        ModuleObj.__init__(self, name)
        self.doc = None
        if self.load_db() == False:
            self.module = self.get_module()
            self.members = self.get_members('dct')             
            self.objtype = str(self.obj).split(' ', 1)[0][1:]
            #self.save_to_db()
        if self.members == {}:
           self.members = self.get_members('dct')     
            
    def save_to_db(self):
        print('Save to DB', self.name)
        db = mdb.db       
        keytypes = {'name':'string', 'module':'string', 'type':'string', 'members':'string', 'data':'string'} 
        lst = []
        data = (self.name, self.module, self.objtype, str(self.members), '')
        lst.append(data)      
        db.from_list('modules', keytypes, lst)

    def load_db(self):       
        print('Load from DB', self.name)       
        res = mdb.fetch('Select * from modules where name = \"%s\"' % self.name)
        if res == None or res == []:
            return False
        data = res[0]
        name, module, objtype, members, data1 = data
        self.module = module
        self.members = eval(members)
        self.objtype = objtype               
        return True
        
    def load_doc_db(self):                 
        res = mdb.fetch('Select doc from doc where name = \"%s\"' % self.name)
        if res == None or res == []:
            return False      
        data = res[0][0]
        text = zlib.decompress(data).decode()
        self.doc = text   
        return True     
    
    def get_list(self):
        return list(dir(self.obj))        
        
    def render_doc(self, title=''):
        if self.doc != None:
            return self.doc
        if self.load_doc_db():
            return self.doc     
        path = '/home/athena/data/help/'    
        filename = path + self.name + '.txt'
        if os.path.exists(filename):
            self.doc = fread(filename)
            return self.doc    
        try:
            #obj, name = pydoc.resolve(self.name)
            print('render ', obj.name)
            obj = self.obj
            text = pydoc.render_doc(obj, title=title)            
            if text == None and obj != None:
                text = self.get_attr('__doc__') 
            self.doc = text    
            return self.doc
        except:
            print(self.name, 'no help doc')  
    
if __name__ == '__main__':    
    mdb = ModuleDB()    
    print(modules)
    #test.search('skimage')
    #db = ModuleDB() 
    #db.gen_function_list(['pydoc']) 
    #print(test.db.search('pydoc'))
    #obj = get_obj('pandas')
    m = ModuleObj('dbm')
    print(m.get_doc())
    print('...')
    



