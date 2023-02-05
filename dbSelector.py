#! /usr/bin/python3.8
import os, sys, re, time
import tkinter as tk
import DB
import aui
from aui import  App, Text
from aui import Layout, Panel
from random import Random
from pprint import pformat

       
class HeadPanel(Panel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.bg = app.cget('bg')
        self.font = ('Mono', 11)
        self.bold = ('Mono', 11, 'bold')
        dbfiles = ['code', 'cache', 'file', 'note']
        self.dboptions = self.add_dbfile_entry(dbfiles, act = self.app.on_select_db) 
        self.textvar = self.add_textlabel()                
        #self.buttons = self.add_buttons2()        

    def add_buttons2(self): 
        app = self.app 
        lst = [('New', app.on_new_item), 
               ('Delete', app.on_delete_item), 
               ('-', 5),
               ('Copy', app.on_copy),
               ('Import', app.on_import),        
               ]  
        buttons = self.add_buttons(lst)     
        return buttons
        
    def on_dbentry(self, event=None):
        name = event.widget.get()
        if not name in self.dboptions.items:
            self.dboptions.add(name)
        
    def add_dbfile_entry(self, items=[], act=None):
        options = self.add_options(label='dbFile:', items=items, act=act)   
        entry = self.add_entry(act=self.on_dbentry)        
        entry.config(width=7)
        self.add_sep()
        return options       
        
    def add_textlabel(self):
        label = self.add_textvar()
        label.config(relief='sunken', height=2, bg='#aaa', font=('Serif', 10))
        return label.textvar
        
    def set_db(self, name):
        #self.dbentry.set_text(name)
        return
        #for bn in self.tabs:
         #   bn.set_state(bn.name==name)

class SelectDB():
    def select_db(self, name):
        self.panel.set_db(name)
        self.set_db(name)
        
    def on_select_db(self, event=None, arg1=None, arg2=None):
        if type(event) == str:
            name = self.getvar(event)
        else:
            name = event.widget.get()   
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
                         
        
class dbSelector(tk.Frame, SelectDB):     
    def __init__(self, master, name='code', table=None, **kw):       
        super().__init__(master, **kw)
        self.size = master.size
        self.app = self
        icon = '/home/athena/data/icon/view.png'
        aui.set_icon(self, icon)
        self.bg = self.cget('bg')
        self.fg = self.cget('highlightcolor')
        self.config(borderwidth=3)
        self.editor = None
        self.root = self.winfo_toplevel()
        self.cdb = DB.open(name)
        self.name = name
        tables = self.cdb.get('tables')
        self.table = table
        self.vars = {'history':[]}
        self.data = []
        self.tree_item = ''
         
        self.init_ui()      
        #self.panel.set_db(name)
        self.panel.dboptions.set(name)
        if self.table != None:
           self.switch_table(table)  
        elif tables != None and len(tables) > 1: 
           self.switch_table(tables[0]) 
        self.actions = {}   
          
    def bind_act(self, event, action):
        self.actions[event] = action
        
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
    
    def update_all(self):
        if self.table == None:
            return
        self.item_names = names = self.table.getnames()        
        self.tree.set_list(names)
        table_name = self.table.name
        name1 = table_name + '-' + str(len(names)) + ' '   
        title = self.name + ':' + name1
        self.panel.textvar.set(name1)
        self.root.title(self.name + '-' + table_name) 

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
        self.msg.set_text(info + '\n')
        self.root.title(info)
        text = self.table.getdata(key)
        if self.editor != None:
            self.editor.set_item(self.table, key, item)    
        if 'select' in self.actions:
            act = self.actions['select']
            act(key, text)     
        
    def on_select(self, event=None):         
        item, key = self.tree.get_focus_item_and_key()
        self.update_item(key, item)       
        
    def on_rename_item(self, event=None):
        p = event.widget.getvar('<<RenameItem>>')
        if p == None:
            return
        item, newkey = p
        self.msg.puts('rename', self.tree.item(item))
        self.tree.set_node_data(item, newkey)             
               
    def init_ui(self):
        x, y = 100, 45
        layout = Layout(self)        
               
        self.panel = HeadPanel(self) 
        layout.add_top(self.panel, y)  
        self.left = tk.Frame(self)
        layout.add_left(self.left, x)  
        
        tree = self.tree = aui.add_tree(self)
        msg = self.msg = aui.add_msg(self)
        layout.add_V2(tree, msg, sep=0.6)
     
        tree.click_select = 'click'   
        tree.bind('<ButtonRelease-1>', self.on_select) 

        self.menubar = Panel(self.left, style='v', size=(100, 1080)) 
        self.menubar.pack()            
        self.set_table_menu()
        self.update()
         
       
def open(name):    
    app = App('DB Table Selector', size=(500, 900))    
    frame = dbSelector(app, 'note', 'Graph')
    app.packfill(frame)
    app.mainloop()   
            
if __name__ == '__main__':   
    open('code')
    #test()

        
    

