import tkinter as tk
from aui import App, aFrame, Notebook, AutoCombo, ScrollBar
from aui import Listbox, ScrollFrame, TextTab, TextUtils, Panel
from DB import SqlDB, db
import pyautogui
from random import Random

class TextEntry(tk.Text, TextUtils):
    def __init__(self, master, text='', **kw):
        super().__init__(master, text, **kw)
        self.mode = 'entry'
        self.rows = []
        self.iscode = False
        self.ln = 1        
        self.init_all()              
        
    def init_code_config(self):
        self.mode = 'code'
        
        self.config(wrap='char')
        self.bind('<FocusIn>', self.on_focus_in)
        self.bind('<FocusOut>', self.on_focus_out)               
        
    def get_data(self):
        if self.edit_modified() == True:
            self.data = self.get_text()
            self.edit_modified(False)            
        return self.data
             
    def set_name(self, name):
        self.mode = 'name'
        self.data = name
        self.insert('1.0', name)
        self.ln = 1
        self.config(height=1)
        self.edit_modified(False)
        
    def set_data(self, text):             
        self.mode = 'text'
        if type(text) != str:
            text = str(text)
        self.ln = text.count('\n') + 1
        self.config(heigh=min(self.ln, 3))        
        self.iscode = db.is_code(text)
        if self.iscode or len(text) > 100:
            self.init_code_config() 
        self.data = text        
        self.set_text(text[0:100])
        self.edit_modified(False)
            
    def init_text(self):
        self.init_pattern()
        self.init_dark_config()
        self.set_text(self.data)    
        self.edit_modified(False)
        
    def on_focus_in(self, event=None):
        n = min(self.ln+2, 30)
        for obj in self.rows:
            obj.config(height=n)
        if self.pattern == None:
            self.init_text()       
        else:
            self.init_dark_config()     
        
    def on_focus_out(self, event=None):
        self.init_config()
        for obj in self.rows:
            obj.config(heigh=3)           

        

class TableView(Panel, ScrollBar):
    def __init__(self, master, cdb, name):
        super().__init__(master)
        self.name = name
        self.cdb = cdb
        self.table = cdb.get_table(name)
        #self.frame = ScrollFrame(master).frame
        self.add_scrollbar(self.base)
        data = self.table.get('*')
        self.data = data
        self.rows = {}
        self.create_rows(self.base, len(data))   
        self.set_dataset(data)        
        self.base.pack(fill='both', expand=True)
        
    def commit(self):
        for i, row in self.rows.items():
            entry, text = row
            if not entry.edit_modified() and not text.edit_modified():
                continue
            name = entry.get_data().strip()
            data = text.get_data()
            print('commit', name, data)            
            if name == '' :
                continue
            if self.name in ['link', 'word']:    
                self.table.adddata(name, data) 
            else:    
                self.table.setdata(name, data) 
    
    def config_row(self, i):
        entry, text = self.rows[i]
        p = self.data[i]
        print(i, len(p))
        if len(p) >= 2:
           name, code = p[0:2]
        else:
           name = p
        entry.set_name(name)           
        text.set_data(code)
        entry.rows = [text, entry]
        text.rows = [text, entry]
        if text.ln >= 3:
            entry.config(height=3)
        
    def set_dataset(self, data):
        n = min(100, len(data))        
        for i in range(n):
            self.config_row(i)
            
    def add_row(self, i=None):
        if i == None:
           i = max(self.rows.keys()) + 1
        entry = TextEntry(self.base, width=15, height=1)
        self.add(entry)
        text = TextEntry(self.base, width=80, height=1)
        self.add(text)
        self.add('\n')
        self.rows[i] = (entry, text) 
        
    def create_rows(self, frame, row, col=2):        
        n = row + 3
        if n > 100:
            n = 100
        n = max(10, n)
        for i in range(n):            
            self.add_row(i)      
       
          
class HeadPanel():
    def init_panel(self, frame):
        bn = Panel(frame, height=1)
        self.add_buttons1(bn) 
        self.add_label(bn)                
        self.add_buttons(bn)         

    def add_buttons(self, bn): 
        bn.add_space(3)  
        bn.add_button('New', self.on_new)
        bn.add_button('Delete', self.on_delete)  
        bn.add_button('Ch', self.on_set_ch)    
        bn.add_space(10)
        button = bn.add_button('   Commit   ', self.on_commit)             
        button.config(font=('bold', 12))
                      
    def add_buttons1(self, bn):
        self.tabs = []
        for s in ['code', 'cache', 'modules', 'file']:
            button = bn.add_button(s, self.on_select_db)
            button.config(font=('Mono', 20))
            self.tabs.append(button)
        
    def add_combo(self, bn):
        combo = bn.add_combo(text='code', values=['code', 'cache', 'modules', 'file'])
        combo.bind('<Return>', self.on_select_db) 
        combo.bind("<<ComboboxSelected>>", self.on_select_db)
        
    def add_label(self, bn):
        bn.pack(fill='x', side='top')
        self.textvar = tk.StringVar()
        self.textvar.set('0')
        label = tk.Label(bn.base, textvariable=self.textvar, anchor='nw', padx=10)
        label.config(font=('Purisa', 15))
        bn.add(label)         
        
    def select_db(self, name):
        for bn in self.tabs:
            if bn.name == name:
                bn.config(foreground='black', background='white', font=('Mono', 20, 'bold'))
            else:
                bn.config(foreground=self.fg, background=self.bg, font=('Mono', 20,))
        self.nb.reset()
        self.set_db(name)
        
    def on_select_db(self, event=None):
        name = event.widget.name
        self.select_db(name)
        
        
class TableEditor(HeadPanel):
    def __init__(self, frame):
        self.master = frame
        #['bd', 'borderwidth', 'class', 'relief', 'background', 'bg', 'colormap', 'container', 'cursor', 'height', 'highlightbackground', 'highlightcolor', 'highlightthickness', 'padx', 'pady', 'takefocus', 'visual', 'width']
        
        self.bg = frame.cget('bg')
        self.fg = frame.cget('highlightcolor')
        self.tk = frame.tk
        self.dbs = {}
        self.pages = {}  
        self.init_panel(frame)            
        self.nb = Notebook(self.master, tab='wn')
        self.nb.bind(self.on_switch_page)
        self.select_db('code')     
        
   
    def set_db(self, name):
        self.name = name
        if name in self.dbs:
            self.cdb = self.dbs[name]
        else:
            self.cdb = SqlDB(name)
            self.dbs[name] = self.cdb
        self.pages = {}
        names = self.cdb.get('tablenames')
        if names == []:
            return
        for name in names:
            page = self.nb.add_page(name)
            page.table = None
            page.tablename = name
            self.pages[name] = page          
        name = Random().choice(names)
        self.init_page_table(name)    
        self.nb.select(self.pages[name])
            
    def init_page_table(self, name):        
        table = self.pages[name].table  
        if table == None:
           table = TableView(self.pages[name], self.cdb, name)
           self.pages[name].table = table
        name1 = name + '-' + str(len(table.data)) + ' '   
        title = self.name + ':' + name1
        self.master.winfo_toplevel().title(title)
        self.textvar.set(name1)
        self.table = table            
        
    def on_switch_page(self, event=None):
        nb = event.widget
        dct = nb.tab('current')
        label = dct['text'].strip()
        self.init_page_table(label)        
        
    def on_new(self, event=None):
        self.table.add_row()
        
    def on_commit(self, event=None):
        print('Commit', 'Filename', self.name, 'TableName', self.table.name)
        self.table.commit()
        
    def on_delete(self, event=None):
        pass
        
    def on_set_ch(self, event=None):
        pyautogui.hotkey('ctrl', 'space')
                              

if __name__ == '__main__':
    app = App(title='Table Editor', size=(1000, 600))
    TableEditor(app)
    app.mainloop()
    




