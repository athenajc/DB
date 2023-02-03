#! /usr/bin/python3.8
import os
import sys
import tk
import time
from pprint import pprint, pformat
import pygments
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter
import DB
import re
from aui import Text, Panel, App
from aui import TextObj 

import nx, plt
from pprint import pprint

dct = {}
dct['global'] = globals()
dct['local'] = locals()  

def invalid_cmd(s):
    s0 = s.strip()
    if s0 == '' or s0[0] == '#':
        return False
    return True      
    
        
class MsgBox(TextObj):
    def __init__(self, master, **kw):
        super().__init__(master, scroll=False, fill=False, **kw)
        pass
        
    def update_tag(self):
        pass
        
    def flush(self, text=''):
        return
        
    def write(self, text):
        if text.strip() == '':
            return
        self.insert('insert', str(text))
        

class TextBox(Panel):
    def __init__(self, tester, name, data, **kw):
        super().__init__(tester.panel, **kw)    
        self.name = name   
        self.data = data
        self.tester = tester
        self.lexer = Python3Lexer()
        self.g_vars = dct['global']
        self.l_vars = dct['local']      
        self.config(border=1, padx=5, pady=5)
        self.pack()        
        self.textbox = textbox = Text(self, scroll=False, fill=False, width=100, height=3)
        textbox.init_dark_config()    
        textbox.config(highlightthickness=0, relief='flat')    
       
        textbox.pack(side='top')
        
        self.msg = MsgBox(self, width=88, height=2)
        self.msg.pack(side='left', expand=True, padx=5)     
        textbox.msg = self.msg   
        button = tk.Button(self, text='Run', command=self.on_exec_cmd, width=7, font=(13))
        button.pack(side='right', expand=True, padx=10)
        self.set_data(data)
        
    def set_data(self, data):          
        if data == '':       
            return       
        self.textbox.set_text(data)  
        self.textbox.update_tag()
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
        if '>>> ' in text:
            text = text.replace('>>> ', '')
            self.textbox.set_text(text)     
        self.tester.savedata(self.name, text)
        lines = text.splitlines()        
        n = min(100, len(lines))
        self.textbox.config(height=n+2) 
        self.textbox.update_tag()
        lst = []
        for s in lines: 
            if 'import ' in s:
                self.try_eval(s, self.g_vars, self.l_vars)   
            if s != '':
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
        if self.msg.get_text() != '':        
            self.msg.puts('\n')
        else:
            self.msg.puts('>>>')
        n = self.msg.get_text().count('\n')        
        n = min(20, n)            
        self.msg.config(height=n+1)
        
    def get_tokens(self, text):
        dct = {}
        lst = list(self.lexer.get_tokens(text))
        for token, content in self.lexer.get_tokens(text):            
             dct[token] = content  
             dct[content] = token
        return dct, lst

    def try_eval(self, s, g_vars, l_vars):             
        try:
           if 'import ' in s:
               r = exec(s, g_vars, l_vars)
           else:
               r = eval(s, g_vars, l_vars) 
           return r
        except Exception as e:
           self.msg.puts(s, e)    

    def try_exec(self, s, g_vars, l_vars):
        try:
            r = exec(s, g_vars, l_vars)    
        except Exception as e:
            self.msg.puts('try_exec1', e)     
           
    def exec_cmd(self, s, g_vars, l_vars):
        if s.strip() == '':
            return
        if s.find('print') == 0:
            s = s[6: -1]
            self.try_exec(s, g_vars, l_vars)
        else:
            self.try_exec(s, g_vars, l_vars)               
            
        
class Tester():
    def __init__(self, app):     
        self.app = app    
        self.bg = '#464d5a'
        app.config(bg = self.bg)
        db = DB.open('code')
        self.table = db.get_table('tmp')
        self.name = self.table.getdata('last', 'tmp')
        self.items = self.table.get('names')
        self.add_name_entry()
        
        panel = Panel(app)
        panel.add_scrollbar()   
        panel.pack(side='top', expand=True, fill='both')
        panel.config(bg='#323c44')
        self.panel = panel
        self.set_table(self.name)            
        self.add_new_button ()
            
    
    def savedata(self, name, text):
        if self.text_dct.get(name) == text:
            return
        self.text_dct[name] = text
        data = pformat(self.text_dct)
        self.table.setdata(self.name, data)
        
    def get_text_db(self, name):        
        data = self.table.getdata(name, {1:''})
        if type(data) == dict:
            return data
        s = data.strip()
        if s == '' or s[0] != '{':
            return {1:''}  
        else:
            return eval(data)
        
    def set_table(self, name):
        self.name = name
        self.text_dct = self.get_text_db(name)
        for name, data in self.text_dct.items():
            textbox = TextBox(self, name, data)        
            self.panel.add(textbox)  
            
    def on_select_combo(self, event=None):
        word = event.widget.get()
        self.panel.reset()
        self.set_table(word)
            
    def add_name_entry(self):       
        panel = Panel(self.app, height=1)
        panel.pack(side='top', fill='x', padx=40, pady=20)        
        combo = panel.add_combo(label='Title Name:   ', values=self.items)
        combo.config(font=('ubuntu Mono', 13), width=30)
        combo.set_text(self.name)
        combo.bind('<Return>', self.on_select_combo) 
        combo.bind("<<ComboboxSelected>>", self.on_select_combo)        
        self.entry = combo
    
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
        self.on_new_text()
        
    def on_new_text(self, event=None):
        name = len(self.text_dct.keys())+1
        self.text_dct[name] = ''
        textbox = TextBox(self, name, '')      
 
        self.panel.add(textbox)  
    

    
if __name__ == '__main__':     
    app = App(title='Test', size=(900, 1000))   
    Tester(app)
    app.mainloop()






