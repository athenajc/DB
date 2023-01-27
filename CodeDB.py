import os
import re
import time
from pprint import pprint
from DB import SqlDB

class CodeDB():     
    def __init__(self, table='example'):   
        self.db = db = SqlDB('code') 
        self.dct = {}    
        self.tables = self.db.get_table_names()
        self.name = table
        self.table = self.select(table)
        
    def create_tables(self, tables=['word', 'link', 'tk', 'ttk', 're', 'aui']):
        for table in tables:
            self.db.create_table(table, dct={'name':'string', 'data':'string'})    
        
    def get(self, table=None):
        if table in ['tablenames', 'table names', 'table_names']:
            return self.db.get_table_names()
        if table == None:
            table = self.table
        res = self.db.fetchall(f"SELECT * FROM {table}", flat=False)
        return res
        
    def getnames(self, table):
        return self.db.fetchall(f'select name from {table}', flat=True)   
        
    def select(self, table):
        self.name = table
        self.table = self.db.get_table(table)
        
    def setdata(self, key, value):    
        self.table.setdata(self.table, key, value)
        
    def getdata(self, key):
        return self.table.getdata(key)
        
    def deldata(self, key):
        self.table.delete_key(self.table, key)
        
    def rename_data(self, key, newkey):
        data = self.getdata(key)
        self.deldata(key)
        self.setdata(newkey, data)       
    
if __name__ == '__main__':   
    db = SqlDB('code')
    table = db.get('link')
    res = table.get('*')
    print(res)


