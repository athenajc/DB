import os
import re
import time
from DB import SqlDB


class CacheDB():    
    db = conn = SqlDB('~/data/cache.db')
    tables = db.get_table_names()    
        
    def create_cache(self, table='cache'):
        self.db.create_table(table, dct={'name':'string', 'data':'string'})         
    
    def add_list(self, table,  lst):
        self.db.from_list(table, {'name':'string'}, lst)
        
    def get_list(self, table):
        self.db.execute('SELECT * FROM %s' % table)  
        
    def set(self, key, data, table='cache'):        
        self.db.setdata(table, key, data)
        
    def get(self, key, table='cache'):
        return self.db.getdata(table, key)
        
    def getword(self, word):
        res = self.db.get('word', word)
        return res
        
    def setword(self, word, data):
        self.db.setdata('word', word, data)
        
    def addword(self, word):
        res = self.getword(word)
        try:
           value = eval(res) + 1
        except:
           value = 0
        self.setword(word, value)
        
    def getwords(self):
        return self.db.fetchall("SELECT * FROM word")







