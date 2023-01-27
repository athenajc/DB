import os
import re
import sys
import tkinter as tk
from tkinter import ttk
import aui
from aui import App, aFrame 
from aui import ImageObj, Text, Layout, Panel
from fileio import get_path, realpath, fread, fwrite
from graphviz import Source
import DB

class Canvas(tk.Canvas):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.filename = None
        self.imageobj = None
        
    def open(self, filename):            
        self.filename = filename  
        self.imageobj = ImageObj(filename)
        self.update_tkimage()   
        
    def update_tkimage(self):
        self.delete('imageobj')
        self.tkimage = self.imageobj.get_tkimage()      
        self.create_image(0,0, image=self.tkimage, anchor='nw', tag='imageobj') 
        
class Editor(Text):
    def __init__(self, master, **kw):       
        super().__init__(master, **kw)
        self.init_dark_config()
        self.tag_config('find', foreground='black', background='#999')

    
class GraphEdit():
    def __init__(self, app):
        w, h = app.size
        self.size = (w, h)
        self.tk = app.tk
        self.init_ui(app)  
        self.add_cmd_buttons()      
        self.editor.open('/home/athena/tmp/Digraph.gv')
        self.update_graph() 
        
    def add_cmd_buttons(self):
        tree = self.tree
        buttons = [('Reset', tree.clear), 
               ('New', lambda event=None: tree.add_dct('', dct)),  
               ('Add', tree.new_node),  
               ('Save', self.save_text),  
                ('Update Graph', self.update_graph)              
               ]
        for cmd, act in buttons:
            self.panel.add_button(cmd, act)
        
    def init_ui(self, app):
        layout = Layout(app)
        self.panel = Panel(app)
        layout.add_top(self.panel, 50)
        f0 = self.editor = Editor(app)
        f1 = self.canvas = Canvas(app)
        msg = self.msg = layout.add_msg(app)    
        tree = self.tree = layout.add_tree(app)
        tree.enable_edit()
        layout.add_set2(objs=(tree, f0, f1, msg))
        return f0, f1, tree    
        
    def save_text(self, event=None):
        editor = self.editor
        text = editor.get_text()
        fwrite(editor.filename, text)
        msg.puts('save', editor.filename, 'ok')
        
    def update_graph(self, event=None):
        editor = self.editor
        text = editor.get_text()
        fwrite(editor.filename, text)
        dot = Source(editor.get_text())        
        fn = dot.render(format='svg')        
        self.canvas.open(fn)
       
    
def dctview(dct=None):
    app = App('Graph Editor', size=(1200, 900))                
    GraphEdit(app)
    app.mainloop() 

    
if __name__ == '__main__':       
     dctview()



