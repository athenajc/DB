#! /usr/bin/python3.8
import os
import sys
import re
import time
import tkinter as tk
import DB
import aui
from aui import  App, aFrame, Text, Notebook, Panel, MenuBar
from random import Random
from pprint import pformat

def check_textlen(text, n):
    for s in text.splitlines():
        if len(s) > n:
            return True
    return False
    

    
class Editor(tk.Frame):
    def __init__(self, master, **kw):       
        super().__init__(master, **kw)
        self.config(padx=10)
        self.tree_item = None
        frame = aui.add_top(master, sep=0.17)
        frame.top.config(padx = 10, pady=5, bg='#232323')  
        self.add_entry(frame.top)
        
        self.text = Text(frame.bottom)
        self.text.init_dark_config()
        self.tag_config = self.text.tag_config
        self.table = None
        self.db_key = 'temp'        
        self.text.add_menu_cmd('Set Nane', self.on_setname)   
        
    def reset(self):
        self.tree_item = None
        self.entry.set('')
        self.text.set_text('')
        
    def add_entry(self, frame):
        frame.config(padx = 10, pady=5, bg='#232323') 
        entry = aui.add_entry(frame, label='Title Name: ')
        entry.add_button('commit', self.on_commit)       
        entry.set('test')
        self.entry = entry
            
    def set_text(self, text):
        text = text.strip()
        if len(text) == 0:
            self.text.set_text('')
            return
            
        if text[0] in ['[', '{']:
            if check_textlen(text, 200):
               text = text.replace(', ', ',    \n')
        else:
            ln = text.count('\n') 
            n = len(text)
            if ln < 3 and n > 200:
                text = pformat(text, width=200)
        self.text.set_text(text)
        
    def set_item(self, table, key, item):        
        self.table = table
        self.db_key = key
        self.tree_item = item
        self.entry.set(key)
        res = self.table.getdata(key)
        if len(res) == 0:
            res = 'empty'
        text = res
        self.set_text(text)
    
    def get_title(self, text):
        for s in re.findall('((?<=class)\s+\w+)|((?<=def)\s+\w+)|([a-zA-Z]\w+)', text):
            return s
        return ''
        
    def get_data(self):
        name = self.entry.get()
        text = self.text.get_text()
        return name, text
        
    def on_savefile(self, event=None):        
        text = self.text.get_text()
        self.table.setdata(self.db_key, text)        
        
    def on_new(self, event=None):
        self.master.event_generate("<<NewItem>>")
        
    def on_commit(self, event=None):
        self.master.event_generate("<<CommitItem>>")
        
    def new_item(self):    
        #key = time.strftime("%Y%m%d_%H%M%S") 
        self.text.set_text('')
        self.entry.set('')
        self.db_key = ''
        self.focus()        
        return ''
           
    def on_setname(self, event=None):
        newkey = self.text.get_text('sel')
        if len(newkey) < 2:
            return        
        self.table.renamedata(self.db_key, newkey)
        self.db_key = newkey
        self.entry.set(newkey)
        self.master.setvar('<<RenameItem>>', (self.tree_item, newkey))
        self.master.event_generate('<<RenameItem>>')  
        

class HeadPanel():
    def __init__(self, frame):
        self.app = frame.app
        self.bg = frame.cget('bg')
        self.font = ('Mono', 15)
        self.bold = ('Mono', 15, 'bold')
        pn = Panel(frame, height=1)
        self.tabs = self.add_db_buttons(pn) 
        self.textvar = self.add_textlabel(pn)                
        self.buttons = self.add_buttons2(pn)        
        pn.pack(fill='x', side='top') 

    def add_buttons2(self, pn): 
        app = self.app 
        lst = [('New', app.on_new_item), 
               ('Delete', app.on_delete_item), 
               ('-', 5),
               ('Copy', app.on_copy),
               ('Import', app.on_import),
               ]  
        buttons = pn.add_buttons(lst)     
        return buttons
                      
    def add_db_buttons(self, pn):
        pn.add_sep()
        lst = []
        for s in ['code', 'cache', 'file', 'note']:
            button = pn.add_button(s, self.app.on_select_db)
            button.config(font=self.font, background='#999')
            lst.append(button)        
        lst[0].set_state(True)
        pn.add_sep()
        return lst        
        
    def add_textlabel(self, pn):
        label = pn.add_textvar()
        label.config(relief='sunken', height=2, bg='#aaa', font=('Serif', 10))
        return label.textvar
        
    def set_db(self, name):
        for bn in self.tabs:
            bn.set_state(bn.name==name)

class SelectDB():
    def select_db(self, name):
        self.panel.set_db(name)
        self.set_db(name)
        
    def on_select_db(self, event=None):
        name = event.widget.name   
        self.select_db(name)
        
    def set_db(self, name):
        self.name = name
        self.cdb = DB.open(name)
        names = self.cdb.get('tables')
        if names == [] or names == None:
            return
        self.set_table_menu()    
        #self.msg.puts('name, names', name, names)
        name = Random().choice(names)
        self.switch_table(name)    
                         
        
class CodeFrame(aFrame, SelectDB):     
    def __init__(self, master, name='code'):       
        super().__init__(master)
        self.app = self
        icon = '/home/athena/data/icon/view.png'
        self.set_icon(icon)
        self.bg = self.cget('bg')
        self.fg = self.cget('highlightcolor')
        self.config(borderwidth=3)
        
        self.root = self.winfo_toplevel()
        self.cdb = DB.open(name)
        self.name = name
        tables = self.cdb.get('tables')
        self.table = None
        self.vars = {'history':[]}
        self.data = []
        self.tree_item = ''
        self.panel = HeadPanel(self)   
        self.init_ui()      
        self.panel.set_db(name)
        if tables != None and len(tables) > 1: 
           self.switch_table(tables[0]) 
        self.editor.bind_all('<<RenameItem>>', self.on_rename_item)    
  
        self.editor.bind_all('<<NewItem>>', self.on_new_item) 
        self.editor.bind_all('<<DeleteItem>>', self.on_delete_item)    
        self.editor.bind_all('<<CommitItem>>', self.on_commit)  
          
    def set_table_menu(self):
        names = self.cdb.get('tables')
        self.menubar.reset()   
        self.menubar.base.config(pady=3)    
        lst = []
        for s in names:
            lst.append((s, self.on_select_table))
        lst.append(('-', 0))
        lst.append(('+', self.on_create_table))    
        btns = self.menubar.add_buttons(lst, style='v')
        self.buttons = btns
        for b in btns:
            b.config(width=7, relief='flat')
        
    def add_table_menu(self, frame):        
        self.menubar = Panel(frame, style='v', size=(100, 1080)) 
        self.menubar.pack(side='top', fill='x', expand=False)
        self.set_table_menu()
        return self.menubar
    
    def update_all(self):
        self.item_names = names = self.table.getnames()        
        self.tree.set_list(names)
        table_name = self.table.name
        name1 = table_name + '-' + str(len(names)) + ' '   
        title = self.name + ':' + name1
        self.panel.textvar.set(name1)
        self.root.title(self.name + '-' + table_name) 
        self.editor.reset()
        
    def switch_table(self, table_name='example'): 
        table_name = str(table_name)   
        self.table = self.cdb.get_table(table_name)   
        for btn in self.buttons:
            btn.set_state(btn.name == table_name)   
        self.update_all()
        
    def on_create_table(self, event=None): 
        table_name = aui.askstring('Input Sting', 'New table name?')
        if table_name == None:
            return
        self.table = self.cdb.create(table_name)
        self.set_db(self.name)
        self.switch_table(table_name)  
            
    def on_select_table(self, event=None):        
        table_name = str(event.widget.name)            
        self.switch_table(table_name)       
        
    def on_new_item(self, event=None):
        self.editor.new_item()
        self.tree_item = ''
        #self.tree.add_node('', name)
        #self.table.adddata(name, '')
        #item = self.tree.focus()
        #self.update_item(name, item)
        
    def on_import(self, event=None):
        files = aui.askopenfiles(ext='py')
        if files == None or len(files) == 0:
            return
        for fp in files:     
            name = os.path.basename(fp.name).split('.', 1)[0]
            text = fp.read()
            self.table.setdata(name, text)  
        self.update_all()
        
    def on_commit(self, event=None):              
        name, text = self.editor.get_data()    
        
        if self.tree_item != '':
            prename = self.tree.get_text(self.tree_item)  
            self.table.delete_key(prename)
            self.msg.puts('on_commit', [prename, name])
        else:
            self.msg.puts('on_commit', [name])    
        self.table.insert_data(name, text)    
        self.item_names = self.table.get('names')
        self.tree.set_list(self.item_names)
        #else:
        #    self.tree_item = self.tree.focus()
        #    self.tree.set_node_data(self.tree_item, name)
        
    def on_copy(self, event=None):
        self.clipboard_clear()
        text = self.textbox.get_text()
        self.clipboard_append(text)   
        
    def on_save(self, event=None):
        self.on_commit(event)
        
    def on_delete_item(self, event=None):
        item = self.tree.focus()
        dct = self.tree.item(item)
        self.msg.puts('delete', item, dct)
        if item == '':
            return    
        key = dct.get('text')
        self.table.deldata(key)    
        self.tree.remove_item(item)
                
    def update_item(self, key, item):
        data = (self.table.name, key, item)
        info = str(data)
        self.msg.set_text(info)
        self.editor.set_item(self.table, key, item)   
        self.root.title(info)
        
    def on_select(self, event=None):         
        item = self.tree.focus() 
        self.tree_item = item
        dct = self.tree.item(item)
        key = dct.get('text')           
        self.update_item(key, item)
        
    def on_add_word(self, event=None):
        word = self.textbox.get_selected_word()
        self.table.adddata('words', word)
        
    def on_rename_item(self, event=None):
        p = event.widget.getvar('<<RenameItem>>')
        if p == None:
            return
        item, newkey = p
        self.msg.puts('rename', self.tree.item(item))
        self.tree.set_node_data(item, newkey)     
                       
    def add_table_tree(self, frame1):
        frame = self.twoframe(frame1, style='left', sep=0.25)   
        self.trees = {}
        self.menubar = self.add_table_menu(frame.left)
        self.tree = tree = self.add_tree(frame.right)
        tree.click_select = 'click'   
        tree.msg = self.msg
        tree.bind('<ButtonRelease-1>', self.on_select) 
        
    def add_textmsg(self, master):     
        frameTB = self.twoframe(master, style='v', sep=0.7)          
        editor = Editor(frameTB.top)        
        self.editor = editor
        textbox = self.editor.text
        msg = self.add_msg(frameTB.bottom)
        textbox.msg = msg
        msg.textbox = textbox
        root = master.winfo_toplevel()
        root.msg = msg
        root.textbox = textbox
        self.msg = msg
        self.textbox = textbox 
        self.editor.msg = msg
    
    def init_ui(self):     
        frameLR = self.twoframe(self, style='h', sep=0.335)           
        self.add_textmsg(frameLR.right)               
        self.add_table_tree(frameLR.left)       
        self.editor.tree = self.tree      
        self.set_table_menu()
         
       
def test():
    app = aui.TopFrame('Sample SQL Editor', size=(1100, 800))    
    app.add(CodeFrame)    
    app.mainloop()     
    
def run(name):
    if len(sys.argv) > 1:
        print(sys.argv)
        name = sys.argv[1] 
    
    app = App('Sample SQL Editor', size=(1300, 900))    
    app.run(CodeFrame, name)   
            
if __name__ == '__main__':   
    run('note')

        
    
