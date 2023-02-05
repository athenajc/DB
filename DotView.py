import os
import re
import sys
import aui
from aui import ttk
from aui import App, aFrame, FigureTk
from aui import Text, Layout, Panel
import DB
import tk, nx, plt
import numpy as np
from pprint import pprint, pformat

        
class Editor(tk.Frame):
    def __init__(self, master, **kw):       
        super().__init__(master, **kw)
        root = master.winfo_toplevel()
        self.app = root.app
        layout = Layout(self)
        self.tree_item = None
        panel = Panel(self, bg='#232323', height=2)
        layout.add_top(panel, 50)
        self.add_entry(panel)
         
        self.text = Text(self, width=120)
        self.text.init_dark_config()        
        
        self.databox = Text(self, width=120)
        layout.add_V2(self.text, self.databox, 0.6)

        self.tag_config = self.text.tag_config
        self.table = None
        self.db_key = 'temp'        
        self.text.add_menu_cmd('Set Nane', self.on_setname)   
        
    def set_name(self, name):
        self.name = name
        self.entry.set(name)
        
    def reset(self, event=None):
        self.tree_item = ''
        self.entry.set('')
        self.text.set_text('')           
        
    def add_entry(self, panel):
        panel.add_space(1)
        panel.add_button('New', self.reset)      
        panel.add_button('Delete', self.on_delete)      
        panel.add_label('  |  ', fg='#aaa')       
        entry = panel.add_entry(label='Name:', width=25)
        panel.add_label('  |  ', fg='#aaa')
        panel.add_button('commit', self.on_commit) 
        panel.add_button('Rename', self.on_rename)
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
            text = pformat(text, width=50, depth=3)
        self.text.set_text(text)
        self.databox.delete('1.0', 'end')
        
    def update_data(self, dct, objs):  
        if objs == []:
            return   
        box = self.databox    
        pretext = box.get_text()
      
        if objs[0][0] in pretext:       
            start = box.search('pos', '1.0')
            for name, xy in objs:
                pos = box.search(name, start)
                if pos == '':
                    continue
                p1, p2 = box.index(pos + ' linestart'), box.index(pos + ' lineend')
                line = box.get(p1, p2)
                a, b = line.split('(')
                line1 = a + str(xy) + ','
                box.replace(p1, p2, line1)
        else:
           text = pformat(dct.get('pos'), width=50, depth=3)
           self.databox.delete('1.0', 'end')
           self.databox.insert('1.0', text)
        
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
        
    def get_data(self):
        name = self.entry.get()
        text = self.text.get_text()
        return name, text
        
    def on_savefile(self, event=None):        
        text = self.text.get_text()
        self.table.setdata(self.db_key, text)        
        
    def on_new(self, event=None):
        self.app.on_new(event)
        
    def on_delete(self, event=None):
        table = self.app.table
        name = self.entry.get() 
        table.deldata(name)
        self.app.update_tree()
        
    def on_commit(self, event=None):
        self.app.commit(event)
        
    def on_rename(self, event=None):
        self.app.rename(self.entry.get())   
        
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
    def __init__(self, canvas):
        self.canvas = canvas
        self.graph = nx.Graph()
        self.dct = {}
        self.colors = {}
        self.color = '#444'
        self.ax = None
        
    def getdct(self):
        pos = {}
        for a, p in self.pos.items():
            pos[a] = tuple(np.round(p, 2))
        dct = {'pos':pos, 'dct':self.dct, 'colors':self.colors}
        return dct
        
    def getdata(self):
        dct = self.getdct()
        return pformat(dct, width=50, depth=3)
        
    def set_obj_color(self, name, color):
        self.colors[name] = color
        
    def canvas_xy(self, p):
        x, y = p
        w, h = 700, 700
        x, y = x*w, h*(1-y)
        x = max(10, x)
        y = max(10, y)
        x = min(w-10, x)
        y = min(h-10, y)
        return x, y
    
    def update_obj(self, objs):        
        for name, xy in objs:
            self.pos[name] = xy
        self.canvas.delete('line')
        pos = self.pos
        for a in pos : 
            p = np.array(pos.get(a))
            lst = self.dct.get(a, [])
            for b in lst:
                p1 = np.array(pos.get(b))
                self.line(p, p1, tag=(a, b))   
        
    def text(self, p, text):
        x, y = self.canvas_xy(p)
        n = len(text)
        fontsize=int(17 - n//3)   
        color = self.colors.get(text, self.color)
        self.canvas.draw_text(x, y, text, anchor='center', color=color, font=(fontsize))
        
    def line(self, p1, p2, tag):
        p3 = (p1 + p2)/2
        p1a = (p1 + p3)/2
        p2a = (p3 + p2)/2
        x1, y1 = self.canvas_xy(p1a)
        x2, y2 = self.canvas_xy(p2a)
        self.canvas.draw_line(x1, y1, x2, y2)        
                
    def draw(self, canvas):
        self.canvas = canvas  
        pos = self.pos
        for a in pos : 
            p = np.array(pos.get(a))
            lst = self.dct.get(a, [])
            for b in lst:
                p1 = np.array(pos.get(b))
                self.line(p, p1, tag=(a, b))            
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
        
    def nx_layout_pos(self, graph):
        pos = nx.spring_layout(graph, center=(0.5, 0.5), scale=0.45) 
        return pos
        
    def set_data(self, data):
        graph = self.graph
        graph.clear()
        dct = self.get_dct(data)
        for a, lst in dct.items():
            graph.add_node(a)
            for b in lst:
                graph.add_edge(a, b)
          
        self.pos = self.nx_layout_pos(self.graph)
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
        self.pos = dct.get('pos', {})
        self.dct = dct.get('dct', {})   
        self.colors = dct.get('colors', {})        
        

from GraphEditor import ImageCanvas        
        
class GraphCanvas(ImageCanvas):
    def __init__(self, master, size, **kw):
        super().__init__(master, **kw)
        self.root = master.winfo_toplevel()       
        self.app = self.root.app
        self.font = ('Mono', 15)
        self.config(borderwidth=1, highlightthickness=1)
        self.create_rectangle(5, 10, 710, 760, outline='#777', fill='#fff', width=3, tag='bg')        
        self.graph = Graph(self)                   
        self.init_selectframe()
        self.set_move_mode()
        self.bind("<<ObjMove>>", self.on_obj_move)
                   
    def reset(self):
        self.clear()
        self.graph = Graph(self)  
        
    def set_color(self, color):
        self.color = color
        if self.obj == None:
            return
        obj = self.obj
        obj.set_color(color)
        if obj.mode == 'text':
             self.graph.set_obj_color(obj.text, color) 
             self.app.databox.puts(obj.text, color)
            
    def on_obj_move(self, event=None):
        def get_xy(x, y):
            x = np.round(x/700, 2)
            y = np.round(1-(y/700), 2)
            return (x, y)
        lst = []
        for obj in self.objs:
            if not obj.modified:
                continue               
            if obj.mode == 'text':
                x, y = obj.get_center()
                xy = get_xy(x, y)
                lst.append((obj.text, xy)) 
                #self.graph.set_node_pos(text, xy)
        #for obj, xy in lst:
        self.graph.update_obj(lst)    
        self.app.editor.update_data(self.graph.getdct(), lst)
        
    def add_figure(self):
        self.figure = FigureTk(self, size=(700, 700), pos=(5, 50))  
        self.ax = self.figure.get_ax()     
            
    def draw(self):
        self.clear()        
        self.graph.draw(self)
        
    def set_text(self, text):        
        self.graph.set_data(text)
        self.draw()
        
    def set_dct(self, text):
        self.graph.set_dct(text)
        self.draw()

        
class CanvasFrame(aFrame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw) 
        self.root = master.winfo_toplevel()       
        self.app = self.root.app
        items = [('Save svg', self.on_save_svg),
                 ('', ''),
                 ('Gen DCT', self.gen_dct_data),
                 ('', ''),
                 ('Update Canvas', self.on_update),
                 ('Update Editor', self.update_editor_data),
                ]   
        layout = Layout(self)
        panel = Panel(self, items=items, height=1)
        layout.add_top(panel, 50)

        panel.config(bg='#353535', relief='sunken')
        
        self.canvas = GraphCanvas(self, size=(700, 700))
        
        panel = Panel(self)
        panel.add_colorbar(self.on_select_color)
        layout.add_H2(self.canvas, panel, 0.7)
        
    def on_update(self, event=None):
        self.app.update_canvas()
        
    def on_save_svg(self, event=None):
        fn = self.root.ask('savefile', ext='img')
        if fn == None or len(fn) == 0:
            fn = '/home/athena/tmp/plt.svg'
        self.canvas.figure.save(fn)    
        
    def gen_dct_data(self, event=None):
        self.app.gen_dct_data()
        
    def update_editor_data(self, event=None):
        self.app.update_editor_data()
        
    def on_select_color(self, event=None):
        color = event.widget.cget('bg')
        self.canvas.set_color(color)
        self.msg.puts(color)
        

class DotView():
    def __init__(self, app):
        w, h = app.size
        self.root = root = app.winfo_toplevel()
        root.app = self
        self.size = (w, h)
        self.tk = app.tk
        self.init_ui(app)  
        #self.add_cmd_buttons()   
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
        self.editor.reset()
        self.canvas.reset()
        self.name = name
        text = self.table.getdata(name)   
        self.editor.set_name(name)
        self.editor.set_text(text)
        
    def init_ui(self, app):
        layout = Layout(app)
        tree = self.tree = app.get('tree')        
                 
        editor = self.editor = Editor(app)
        f01 = app.get('frame')
        layout.add_H3(tree, editor, f01, (0.14, 0.5))          
        
        canvas =  CanvasFrame(f01)      
        msg = self.msg = f01.get('msg')  
        layout2 = f01.get('layout')
        layout2.add_V2(canvas, msg, 0.7)
        
        editor.msg = canvas.msg = msg
        editor.app = canvas.app = self
        self.canvas = canvas.canvas
        self.root.msg = msg
        self.databox = self.editor.databox
        self.canvas.msg = msg
        
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
        
    def rename(self, newname):
        table = self.table      
        table.renamedata(self.name, newname)   
        self.update_tree()
        self.set_item(newname)     
        
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
        
    def update_editor_data(self, event=None):
        if not '.dct' in self.name:
            return self.gen_dct_data()
        data = self.canvas.graph.getdata()
        self.editor.set_text(data)  
        self.table.setdata(self.name, data) 
           
    def on_new(self, event=None):
        self.editor.reset()        
        
    
            
    
if __name__ == '__main__':       
    app = App('Graph Editor', size=(1800, 1000))                
    DotView(app)
    app.mainloop() 



