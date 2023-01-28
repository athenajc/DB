import os
import sys
import tkinter as tk
from tkinter import ttk
import time
from pprint import pprint, pformat
import DB
import re
from ui import *

dct = {}
dct['global'] = globals()
dct['local'] = locals()  


class TextBox(tk.Frame):
    def __init__(self, tester, name, data, **kw):
        super().__init__(tester.panel, **kw)    
        self.name = name   
        self.data = data
        self.tester = tester
        self.g_vars = dct['global']
        self.l_vars = dct['local']      
        self.config(border=1, padx=10, pady=5)
        self.pack()        
        self.textbox = TextObj(self, width=100, height=3)
        self.textbox.init_dark_config()
        self.textbox.pack(side='top',)
        
        self.msg = MsgBox(self, width=85, height=1)
        self.msg.pack(side='left', expand=True)        
        button = tk.Button(self, text='Run', command=self.on_exec_cmd, width=10)
        button.pack(side='right', expand=True)
        self.set_data(data)
        
    def set_data(self, data):          
        if data == '':       
            return       
        self.textbox.set_text(data)  
        n = min(100, data.count('\n') )
        self.textbox.config(height=n+2)
               
    def eval_print(self, s):
        r = self.try_eval(s, self.g_vars, self.l_vars)
        if r != None:
            self.msg.puts('>>> ' + s, end='')
            self.msg.puts_tag(  str(r), 'bold')
                
    def on_exec_cmd(self, event=None): 
        self.msg.clear_all()
        self.msg.update()
        sys.stdout = self.msg
        text = self.textbox.get_text()     
        self.tester.savedata(self.name, text)
        lines = text.splitlines()        
        n = min(100, len(lines))
        self.textbox.config(height=n+2) 
        self.textbox.update_tag()
        lst = []
        for s in lines: 
            s0 = s.strip()           
            if s0[0] == '#':
                continue
            if s.find('import') >= 0:
               self.try_exec1(s, self.g_vars, self.l_vars)                          
            elif s != '':
                lst.append(s)
        text = '\n'.join(lst)          
        self.exec_cmd(text, self.g_vars, self.l_vars)   
        for s in lst:
            if s in self.g_vars or s in self.l_vars:
                self.eval_print(s)
            elif '=' in s or '(' in s:
                continue                
            else:
                self.eval_print(s)    
        self.msg.puts('>>>')
        n = self.msg.get_text().count('\n')        
        n = min(20, n)            
        self.msg.config(height=n+1)

    def try_eval(self, s, g_vars, l_vars):    
        if s.strip() == '':
            return    
        try:
           r = eval(s, g_vars, l_vars) 
           #self.msg.puts(r)
           return r
        except Exception as e:
           self.msg.puts(e)
                   
    def try_exec(self, s, g_vars, l_vars):
        try:
           r = exec(s, g_vars, l_vars)         
        except Exception as e:
           self.msg.puts(e)
        self.try_eval(s, g_vars, l_vars)            

    def try_exec1(self, s, g_vars, l_vars):
        try:
            r = exec(s, g_vars, l_vars)    
        except Exception as e:
            self.msg.puts(e)     
           
    def exec_cmd(self, s, g_vars, l_vars):
        if s.strip() == '':
            return
        if s.find('print') == 0:
            s = s[6: -1]
            self.try_exec1(s, g_vars, l_vars)
        else:
            self.try_exec1(s, g_vars, l_vars)               
            

class Tester():
    def __init__(self, app):     
        self.app = app    
        self.bg = '#464d5a'
        app.config(bg = self.bg)
        self.name = 'tmp'
        self.add_name_entry()
        
        panel = CodePanel(app)
        panel.add_scrollbar()   
        panel.pack(side='top', expand=True, fill='both')
        self.panel = panel
        self.text_dct = self.get_text_db()
        for name, data in self.text_dct.items():
            textbox = TextBox(self, name, data)        
            panel.add(textbox)  
            
        self.add_new_button ()
            
    def savedata(self, name, text):
        if self.text_dct.get(name) == text:
            return
        self.text_dct[name] = text
        data = pformat(self.text_dct)
        self.table.setdata(self.name, data)
        
    def get_text_db(self):
        db = DB.open('code')
        self.table = db.get_table('tmp')
        self.name = self.table.getdata('last', 'tmp')
        text_dct = self.table.getdata(self.name, {1:''})
        if text_dct.strip()[0] == '{':
            text_dct = eval(text_dct)
        else:
            text_dct = {1:''}
        return text_dct
            
    def add_name_entry(self):
        frame = tk.Frame(self.app)
        frame.pack(side='top', fill='x', padx=40, pady=20)
        button = tk.Button(frame, text='Reset', command=self.on_reset)
        entry = add_entry(frame, label='Title Name: ')
        entry.set(self.name)
        self.entry = entry
    
    def add_new_button(self):
        frame = tk.Frame(self.app, bg=self.bg)
        frame.pack(side='top', fill='x', padx=40, pady=20)
        button = tk.Button(frame, text='Reset', command=self.on_reset)
        button.pack(side='left')
        button = tk.Button(frame, text='New +', command=self.on_new_text, width=20)
        button.pack(side='right', padx=30)
        
    def on_reset(self, event=None):
        self.panel.reset()
        self.text_dct = {1:''}
        self.name = time.strftime("%Y%m%d_%H%M%S") 
        
    def on_new_text(self, event=None):
        name = len(self.text_dct.keys())+1
        self.text_dct[name] = ''
        textbox = TextBox(self, name, '')        
        self.panel.add(textbox)  
    

    
if __name__ == '__main__':     
    app = App(title='Test', size=(900, 1000))   
    Tester(app)
    app.mainloop()






