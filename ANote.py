#! /usr/bin/python3.8
import os
import re
import tkinter as tk
from tkinter import ttk
from aui import  aFrame, Text
from fileio import fread
from aui.FileMenuActions import MenuActions
import jieba
import jieba.posseg as pseg
import random
from DB import SqlDB, CacheDB, db

class NoteDB(CacheDB):     
    def __init__(self):    
        super().__init__()
        self.dct = {}    
        tables = self.db.get_table_names()
        if not 'note' in tables:
           self.db.create_table('note', dct={'name':'string', 'data':'string'})    
            
    def setnote(self, key, value):    
        self.db.setdata('note', key, value)
        
    def getnote(self, key):
        return self.db.getdata('note', key)
        
    def delnote(self, key):
        self.db.delete_key('note', key)
                
    def renamenote(self, key, newkey):
        self.db.renamedata('note', key, newkey)    
        
  
cdb = NoteDB()
path = cdb.get('a-note.path')

class Editor(Text):
    def __init__(self, master, **kw):       
        super().__init__(master, **kw)
        self.init_markdown()
        self.bind('<KeyRelease>', self.on_update_text)    
        self.add_menu_cmd('Add word', self.on_add_word)
        self.add_menu_cmd('Rename as Selected', self.on_rename_as_selected)
          
    def on_add_word(self, event=None):
        word = self.get_selected_word()
        cdb.addword(word)

    def on_rename_as_selected(self, event=None):
        text = self.get_text('sel')
        if len(text) < 2:
            return
        self.setvar('<<RenameFile>>', (self.filename, text))
        self.event_generate('<<RenameFile>>')          
        
    def init_markdown(self):
        n = 14
        self.config(font=('Mono', n))
        self.pattern = '(?P<h3>###.+)|(?P<h2>##.+)|(?P<h1>#.+)|(?P<bold>\*.+?\*)'
        self.config(foreground='#c8ced9')
        self.config(background='#323c44')         
        self.config(insertbackground="#fa5")
        self.tag_config('bold', font=('Mono', n+1, 'bold'), foreground='#e8eef9', background='#323c44')
        self.tag_config('h1', font=('Mono',n+6), foreground='#e8eef9')
        self.tag_config('h2', font=('Mono',n+4), foreground='#dfdeef')
        self.tag_config('h3', font=('Mono',n+2), foreground='#d8dee9')
        self.tag_config('+', font=('Mono',n+2), foreground='#d8dee9')
        self.tag_config('str1', font=('Mono',n+1),foreground='#99c794')
        self.tag_config('str2', font=('Mono',n+2),foreground='#99c794')
        self.tag_config('str3', font=('Mono',n+2),foreground='#99c794')
        self.tag_config('hide', font=(8), foreground='#323c44')    
        self.tag_map = {'#':'h1', '##':'h2', '###':'h3', '+':'+', '@':'h2', '!':'h3', '*':'bold'}    
        self.key_tagnames = ['h1', 'h2', 'h3', 'hide', 'bold', 'str1', 'str2', 'str3', '+']   
        p0 = '(?P<bold>\*.+\*)|(?P<str1>\'[^\']+\')|(?P<str2>\"[^\"]+\")|(?P<str3>\([^\)]+\))'  
        self.tag_pattern = re.compile(p0)
        
    def tag_line(self, i, line):        
        ln = str(i+1) + '.'   
        m = re.search('^\s*(\#+|\+|\@|\!)', line)            
        if m: 
            s = m.group(1)
            tag = self.tag_map.get(s, '')
            n = len(s)
            start = m.start() + n - 1
            self.tag_add('hide', ln+ f"{start}", ln +f"{start+n}") 
            self.tag_add(tag, ln+f"{start+n}", ln+'end')        
            return  
        for m in re.finditer(self.tag_pattern, line):
            a, b= m.start(), m.end()            
            for tag, s in m.groupdict().items():
                if s == None:  
                    continue
                if tag != 'bold':
                    p1, p2 = ln+str(a), ln+str(b)
                    self.tag_add(tag, p1, p2)
                else:
                    p1, p2, p3, p4 = ln+str(a), ln+str(a+1), ln+str(b-1), ln+str(b)
                    self.tag_add('hide', p1, p2)
                    self.tag_add('hide', p3, p4)
                    self.tag_add('bold', p2, p3)
                
    def on_update_text(self, event=None):
        self.config(font=('Mono', 13))
        for tag in self.key_tagnames:
            self.tag_remove(tag, '1.0', 'end')
        text = self.get_text()
        text = text.replace('“', '\"').replace('”', '\"')
        for s in '『《「（{[':
            if s in text:
                text = text.replace(s, '(')
        for s in '』》」）}]':
            if s in text:
                text = text.replace(s, ')')                
        for i, line in enumerate(text.splitlines()):     
             self.tag_line(i, line)   
             
    def split_text(self, event=None):
        text = self.get_text()
        lines = text.splitlines()
        lst = []
        for line in lines:
            seg_list = jieba.cut(line, cut_all=False)
            lst.append(" ".join(seg_list))
        text = '\n'.join(lst)    
        self.set_text(text)     
        

class NotebookFrame(aFrame):
    def __init__(self, master, cnf={}, **kw):
        super().__init__(master)
        self.pages = {}
        notebook = ttk.Notebook(self)
        notebook.pack(fill = 'both', expand=True)
        self.notebook = notebook
        notebook.bind('<ButtonRelease-1>', self.switch_page)
        self.pack(fill = 'both', expand=True)
        
    def switch_page(self, event=None):
        dct = self.notebook.tab('current')
        label = dct['text'].strip()
        #print('label', label)

    def add_page(self, label, widget=None):
        frame = aFrame(self.notebook)
        frame.pack(fill='both', expand=True)         
        if widget != None:
            widget.notepage = frame
            widget.label = label                       
        self.notebook.add(frame, text=label.center(17))        
        n = len(self.pages)        
        self.notebook.select(n)        
        return frame
                

class ANoteFrame(aFrame, MenuActions):     
    def __init__(self, master):       
        super().__init__(master)
        self.vars = {'history':[]}
        self.init_ui()        
        
        os.chdir(path)
        self.set_path(path)             
        fn = random.choice(os.listdir(path))
        self.load_file(fn)
        self.bind_all('<<SelectFile>>', self.on_select_file)  
        
    def load_file(self, fn):
        self.filename = fn
        self.textbox.open(fn)   
        self.textbox.on_update_text()     
        self.set_filename(fn)
        
    def on_select_file(self, event):     
        path, tag = event.widget.getvar('<<SelectFile>>')
        if tag == 'file':
           self.open_file(path)           
           
    def _add_textmsg(self, master):     
        frameTB = self.twoframe(master, style='v', sep=0.7)   
        self.notebook = NotebookFrame(frameTB.top)
        page = self.notebook.add_page('NoteText')        
        self.textbox = textbox = Editor(page)
        self.msg = msg = self.add_msg(frameTB.bottom)
        self.textbox.msg = msg
        self.tk.setvar('msg', msg)        
        msg.textbox = textbox
        root = master.winfo_toplevel()
        root.msg = msg
        root.textbox = textbox
        return textbox, msg
        
    def init_ui(self):
        mframe = self.twoframe(self, style='leftbar', sep=0.05)        
        self.add_menubar(mframe.left)                   
        frameLR = self.twoframe(mframe.right, style='h', sep=0.335)        
        self._add_textmsg(frameLR.right)       
        self.filetree = tree = self.add_filetree(frameLR.left)
        tree.click_select = 'click'   
        tree.msg = self.msg      

    def set_path(self, path):
        self.filetree.set_path(path)            

                
if __name__ == '__main__':   
    from aui import App
    icon = '~/data/icon/a-note.png'
    frame = App('A Notebook', size=(1920, 1080), icon=icon, Frame=ANoteFrame)
    frame.mainloop()
    



