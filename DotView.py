import os
import re
import sys
import aui
from aui import ttk
from aui import App, aFrame, FigureTk
from aui import Text, Layout, Panel
import DB
import pydot
import tk, nx, plt
import numpy as np
from pprint import pprint, pformat


class Editor(tk.Frame):
    def __init__(self, master, **kw):       
        super().__init__(master, **kw)
        root = master.winfo_toplevel()
        self.app = root.app
        self.config(padx=10)
        self.tree_item = None
        frame = tk.Frame(self)
        frame.config(pady=5, bg='#232323')  
        self.add(frame)
        self.add_entry(frame)

        self.text = Text(self, width=120)
        self.text.init_dark_config()
        #self.add(self.text)
        self.text.pack(fill='both', expand=True)
        self.tag_config = self.text.tag_config
        self.table = None
        self.db_key = 'temp'        
        self.text.add_menu_cmd('Set Nane', self.on_setname)   
        
    def set_name(self, name):
        self.name = name
        self.entry.set(name)
        
    def add(self, obj):
        obj.pack(fill='x')
        
    def reset(self):
        self.tree_item = ''
        self.entry.set('')
        self.text.set_text('')
        
    def add_entry(self, frame):
        frame.config(pady=5, bg='#232323') 
        entry = aui.add_entry(frame, label='Name:', width=20)
        entry.add_button('commit', self.on_commit)               
        self.entry = entry
             
    def get_text(self):
        return self.text.get_text()
        
    def set_text(self, text):
        text = text.strip()
        if len(text) == 0:
            self.text.set_text('')
            return
        ln = text.count('\n') 
        n = len(text)    
        if ln < 3 and n > 200:
            text = pformat(text, width=30, depth=3)
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
        self.app.on_new(event)
        
    def on_commit(self, event=None):
        self.app.commit(event)
        
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
        self.app.setvar('<<RenameItem>>', (self.tree_item, newkey))
        self.app.event_generate('<<RenameItem>>')  

 
class Graph():
    def __init__(self):
        self.graph = nx.Graph()
        self.dct = {}
        self.ax = None
        
    def getdata(self):
        pos = {}
        for a, p in self.pos.items():
            pos[a] = tuple(np.round(p, 2))
        dct = {'pos':pos, 'dct':self.dct}
        return pformat(dct, width=30, depth=3)
        
    def text(self, p, text):
        x, y = p 
        n = len(text)
        self.ax.text(x, y, text, ha='center', va='center',fontsize=int(17 - n//3))
        
    def line(self, p1, p2):
        p3 = (p1 + p2)/2
        p1a = (p1 + p3)/2
        p2a = (p3 + p2)/2
        self.fig.add_line(p1a, p2a)
        
    def nxdraw(self, fig):
        nx.draw(self.graph, self.pos, ax=fig.ax, with_labels=True, 
                node_color='#dedede', node_size=1000)
                
    def draw(self, fig):
        self.ax = fig.ax
        self.fig = fig
        pos = self.pos
        for a in pos : 
            p = np.array(pos.get(a))
            lst = self.dct.get(a, [])
            for b in lst:
                p1 = np.array(pos.get(b))
                self.line(p, p1)
            
        for a in pos : 
            self.text(pos.get(a), a)
            
    def get_dct(self, data):
        dct = {}
        for s in re.findall('[\w\_]+', data):
            dct[s] = []
            
        for line in data.splitlines():
            if not '-' in line:
                continue
            tokens = [s.strip() for s in line.split('-')]
            #for s in line.split('-'):
            #    tokens.append(s.strip())
            for a, b in zip(tokens, tokens[1:]):        
                if ',' in b:
                    for s in b.split(','):                    
                        dct[a].append(s.strip())
                else:        
                    dct[a].append(b)
        dct1 = {}
        for a, lst in dct.items():            
            if lst != []:
                dct1[a] = lst
        return dct1
        
    def set_data(self, data):
        graph = self.graph
        graph.clear()
        dct = self.get_dct(data)
        for a, lst in dct.items():
            graph.add_node(a)
            for b in lst:
                graph.add_edge(a, b)
        pos = nx.spring_layout(self.graph, center=(0.5, 0.5), scale=0.45)    
        self.pos = pos        
        self.dct = dct                 
        return graph
        
    def set_dct(self, data):
        if not '{' in data or not '}' in data or not 'dct' in data:
            return
        try:    
            dct = eval(data)
        except Exception as e:
            self.msg.puts('Error set_dct', e)
            return
        self.pos = dct.get('pos')
        self.dct = dct.get('dct')
        
    
        
class GraphCanvas(tk.Canvas):
    def __init__(self, master, size, **kw):
        super().__init__(master, **kw)
        self.config(borderwidth=1, highlightthickness=1)
        self.create_rectangle(5, 50, 699, 699, outline='#777', width=3)
        items = [('Save svg', self.on_save_svg),
                 ('', ''),
                 ('Update', self.on_update)
                ]
        panel = Panel(self, items=items, style='h', height=1)
        panel.config(bg='#353535', relief='sunken')
        panel.place(x=0, y=0, relwidth=1, height=46)
        
        colors = range(20)
        self.figure = FigureTk(self, size=(694, 649), pos=(5, 50))  
        self.graph = Graph()           
        self.ax = self.figure.get_ax()       
                   
    def on_update(self, event=None):
        self.app.update_canvas()
        
    def on_save_svg(self, event=None):
        fn = self.winfo_toplevel().ask('savefile', ext='img')
        if fn == None or len(fn) == 0:
            fn = '/home/athena/tmp/plt.svg'
        self.figure.save(fn)    
        
    def from_dot(self, data):        
        s = data.strip()
        if s == '':
            return
        return self.get_node_list(s)  
   
    def set_text(self, text):
        self.ax.clear() 
        self.graph.set_data(text)
        self.graph.draw(self.figure)
        self.figure.update()
        #self.msg.pprint(self.graph.pos)
        
    def set_dct(self, text):
        self.ax.clear() 
        self.graph.set_dct(text)
        self.graph.draw(self.figure)
        self.figure.update()
        
    
class DotView():
    def __init__(self, app):
        w, h = app.size
        root = app.winfo_toplevel()
        root.app = self
        self.size = (w, h)
        self.tk = app.tk
        self.init_ui(app)  
        self.add_cmd_buttons()   
        db = DB.open('note')
        self.table = table = db.get('Dot')
        names = table.get('names')
        self.tree.set_list(names)
        self.set_item(names[0])
        self.tree.bind_click(self.on_select)

    def on_select(self, event):
        item, key = self.tree.get_focus_item_and_key() 
        self.set_item(key)
        self.update_canvas()
            
    def set_item(self, name):
        self.name = name
        text = self.table.getdata(name)   
        self.editor.set_name(name)
        self.editor.set_text(text)
        
    def init_ui(self, app):
        layout = Layout(app)
        self.panel = Panel(app)
        layout.add_top(self.panel, 50)
        tree = self.tree = app.get('tree')        
        msg = self.msg = app.get('msg') 
        frame2 = app.get('frame')
        layout.add_HV(tree, frame2, msg, (0.14, 0.8))
          
        f0 = self.editor = Editor(frame2)
        f1 = self.canvas = GraphCanvas(frame2, size=(700, 700))
        layout2 = frame2.get('layout')
        layout2.add_H2(f0, f1, 0.37)
        f0.msg = f1.msg = msg
        f0.app = f1.app = self
        
    def get_text(self):
        return self.editor.get_text()
        
    def update_canvas(self):
        text = self.get_text()
        if self.name.endswith('.dct'):
            self.canvas.set_dct(text)
        else:
            self.canvas.set_text(text)
        
    def update_tree(self):        
        names = self.table.get('names')
        self.tree.set_list(names) 
        
    def commit(self, event=None):
        text = self.get_text()
        name = self.editor.entry.get() 
        self.table.setdata(name, text)       
        self.name = name
        self.update_canvas()
        self.update_tree()
        
    def on_update(self, event=None):
        self.update_canvas()  
        
    def gen_dct_data(self, event=None):
        data = self.canvas.graph.getdata()
        name = self.name + '.dct'
        self.table.setdata(name, data)  
        self.update_tree()      
        
    def on_new(self, event=None):
        self.editor.reset()        
        
    def add_cmd_buttons(self):
        tree = self.tree
        buttons = [('Reset', tree.clear), 
               ('New', self.on_new),         
               ('Gen DCT', self.gen_dct_data),
              # ('Update Canvas', self.on_update),                 
               ]
        for cmd, act in buttons:
            self.panel.add_button(cmd, act)
            
    
if __name__ == '__main__':       
    app = App('Graph Editor', size=(1200, 900))                
    DotView(app)
    app.mainloop() 



