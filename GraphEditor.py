#! /usr/bin/python3.8
import sys
import tkinter as tk
from aui import App, aFrame
from PIL import ImageFont
from aui import ImageObj
import DB               

class CanvasFrame1(aFrame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        layout = self.get('layout')
        panel = self.get('panel', height=1)
        layout.add_top(panel, 50)
        self.add_toolbar(panel)        
        from aui.ImageCanvas import ImageCanvas
        canvas = ImageCanvas(self, bg='#f5f3f3', size=(1024, 768))
        self.canvas = canvas        
        from aui.dbEditorFrame import dbEditorFrame        
        self.editor = dbEditorFrame(self)
    
        self.editor.text.bind('<ButtonRelease-1>', self.get_sel_text)
        self.editor.puts('紅塵-黃-綠-藍-電子')
        canvas.editor = self.editor
        layout.add_V2(canvas, self.editor, 0.6)
        
    def add_toolbar(self, tb):        
        lst = [('Clear', self.on_clear), ('-', ''),
               ('Text', self.on_set_mode), 
               ('Line', self.on_set_mode),
               ('Pen',  self.on_set_mode),
               ('Move', self.on_set_mode), 
               ('-', ''),
               ('To Editor', self.to_editor),
               ('-', ''),
               ('Save Image', self.on_save)
               ]               
        self.buttons = tb.add_buttons(lst)   
        self.buttons[0].set_state(True)
        self.label = tb.add_label(text = 'test draw 中文 text')
         
    def to_editor(self, event=None):
        self.canvas.to_editor(event)
        
    def on_save(self, event=None):
        self.canvas.save_image()
        
    def on_clear(self, event=None):
        self.canvas.clear()
        
    def on_set_mode(self, event=None):
        button = event.widget
        for bn in self.buttons:
            bn.set_state(False)
        button.set_state(True)
        self.canvas.set_mode(button.text)
        
    def set_input_text(self, text):
        if '\n' in text:           
            label = text.replace('\n', ',')[0:100]
        else:
            label = text
        self.label.config(text=label, fg=self.canvas.color)
        self.canvas.set_input_text(text)
        
    def get_sel_text(self, event=None):
        text = self.editor.get_text('sel')                
        self.set_input_text(text)
        
    def set_data(self, key, text):
        self.set_input_text(key)
        #self.editor.set_text(text + '\n')        
        
    def set_color(self, color):
        self.canvas.set_color(color)
        self.label.config(fg=color)



class DrawText(aFrame):
    def __init__(self, app, **kw):
        super().__init__(app, **kw)
        self.root = root = app.winfo_toplevel()
        layout = self.layout = self.get('layout')

        from aui.ImageCanvas import CanvasFrame      

        canvas = CanvasFrame(self) 
        selector = canvas.add_db_panel(self, table=('note', 'Graph')) 
        self.tk.setvar('selector', selector)
        self.editor = editor = canvas.add_editor(self)
        self.msg = editor.msg
        layout.add_H3(selector, editor, canvas, sep=(0.1, 0.4))

        root.editor = canvas.editor
        root.canvas = canvas.canvas
        root.selector = selector
        self.msg = root.msg = editor.msg
        sys.stdout = self.msg
    
    def on_select_color(self, event=None):
        color = event.widget.cget('bg')
        self.canvas.set_color(color)
        self.msg.puts(color)
        
    def on_select(self, key, text):
        self.canvas.set_input_text(key)    
         
    
if __name__ == '__main__':
    app = App('Text to Canvas', size=(1920, 1080))    
    DrawText(app)    
    app.mainloop()

