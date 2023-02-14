#! /usr/bin/python3.8
import os, sys, re
from aui import  aFrame, Panel
from random import Random
from pprint import pformat
import DB       
        
class HeadPanel(Panel):
    def __init__(self, master, bg=None):
        super().__init__(master, bg=bg, height=1)
        self.app = master.app
        if bg == None:
            bg = master.cget('bg')
        self.bg = bg
        
        self.font = ('Mono', 12)
        self.bold = ('Mono', 12, 'bold')
        
        self.tabs = self.add_db_buttons(self) 
        self.textvar = self.add_textlabel(self)                
        self.buttons = self.add_buttons2(self)                

    def add_buttons2(self, pn): 
        app = self.app 
        lst = [('Update', app.on_update_db),  
               ('Import', app.on_import),        
               ]  
        buttons = pn.add_buttons(lst)     
        return buttons
                      
    def add_db_buttons(self, pn):
        lst = []
        for s in ['code', 'cache', 'file', 'note']:
            button = pn.add_button(s, self.app.on_select_db)
            button.config(font=self.font, background='#999')
            lst.append(button)        
        lst[0].set_state(True)       
        return lst        
        
    def add_textlabel(self, pn):
        label = pn.add_textvar()
        label.config(relief='sunken', height=1, bg='#aaa', font=('Serif', 10))
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
        
    def set_db(self, name, table_name=None):
        self.name = name
        self.db = DB.open(name)
        names = self.db.get('tables')
        if names == [] or names == None:
            return
        if table_name == None:
            table_name = Random().choice(names)    
        self.panel.set_db(name)    
        self.set_table_menu(table_name)    
        self.switch_table(table_name)  
                         
        
class CodeFrame(aFrame, SelectDB):     
    def __init__(self, master, name='code', table=None):       
        super().__init__(master)
        self.size = master.size
        self.app = self
        self.root = master.winfo_toplevel()
        icon = '/home/athena/data/icon/view.png'
        self.set_icon(icon)
        self.bg = self.cget('bg')
        self.fg = self.cget('highlightcolor')
        self.config(borderwidth=3)
        
        self.root = self.winfo_toplevel()
        self.db = DB.open(name)
        self.name = name
        tables = self.db.get('tables')
        self.table = None
        self.vars = {'history':[]}
        self.data = []
        self.tree_item = ''
         
        self.init_ui()      
        self.set_db(name, table)
        self.update_all()
        self.editor.bind_all('<<RenameItem>>', self.on_rename_item)    
  
        self.editor.bind_all('<<NewItem>>', self.on_new_item) 
        self.editor.bind_all('<<DeleteItem>>', self.on_delete_item)    
        self.editor.bind_all('<<CommitItem>>', self.on_commit)  
          
    def set_table_menu(self, tablename=None):
        names = self.db.get('tables')
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
        self.table = self.db.get_table(table_name)   
        for btn in self.buttons:
            btn.set_state(btn.name == table_name)   
        #self.update_all()
        
    def on_create_table(self, event=None): 
        table_name = self.root.askstring('Input Sting', 'New table name?')
        if table_name == None:
            return
        self.table = self.db.create(table_name)
        self.set_db(self.name)
        self.switch_table(table_name)  
        self.update_all()
            
    def on_select_table(self, event=None):        
        table_name = str(event.widget.name)            
        self.switch_table(table_name)    
        self.update_all()   
        
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
        try:
            prename = self.tree.get_text(self.tree_item)  
        except:
            prename = ''   
        if prename != '':
            self.table.delete_key(prename)
            self.msg.puts('on_commit', [prename, name])
        else:
            self.msg.puts('on_commit', [name])    
        self.table.insert_data(name, text)    
        self.item_names = self.table.get('names')
        self.tree.set_list(self.item_names)
        
    def on_copy(self, event=None):
        self.clipboard_clear()
        text = self.editor.text.get_text()
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
        
    def on_update_db(self, event=None):
        DB.update_all()
                
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
        
    def get_db_table(self):
        return self.table
        
    def update_tree(self):
        names = self.table.getnames()        
        self.tree.set_list(names)
        
    def init_ui(self):
        frame = self.get('frame')
        frame.app = self
        layout = frame.get('layout')
        self.panel = HeadPanel(frame, bg=self.cget('bg'))  
        layout.add_top(self.panel, 45)  
        
        self.menubar = Panel(frame, style='v', size=(100, 1080), width=12)
        layout.add_left(self.menubar, 100)     
        tree = self.tree = frame.get('tree')   
        layout.add_box(tree)
        
        from aui.dbEditorFrame import dbEditorFrame
        editor = self.editor = dbEditorFrame(self, databox='msg')      
        editor.entry.config(width=42)    
        editor.panel.add_button('Copy', self.on_copy)
        editor.app = self
        editor.get_db_table = self.get_db_table
        
        self.layout = self.get('layout')
        self.layout.add_H2(frame, editor, sep=0.25)
        tree.click_select = 'click'   
        tree.msg = self.msg = editor.msg
        tree.bind('<ButtonRelease-1>', self.on_select) 

         

def test():
    from aui import App       
    app = App()    
    frame = aui.TopFrame()    
    panel = frame.add('panel')
    panel.pack(fill='both', expand=True)   
    frame1 = CodeFrame(panel)
    frame1.pack(fill='both', expand=True)   
    app.mainloop()     
    
def run(name, table=None):
    if len(sys.argv) > 1:
        print(sys.argv)
        name = sys.argv[1] 
    from aui import App       
    app = App('Sample SQL Editor', size=(1600, 1000))    
    frame = CodeFrame(app, name, table)
    frame.pack(fill='both', expand=True)
    app.mainloop()   
            
if __name__ == '__main__':   
    run('note', 'note')


        
    

