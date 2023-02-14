from aui.Menu import Panel
from aui.TextObj import TextEntry
from aui import App

class TableView(Panel):
    def __init__(self, master, table):
        super().__init__(master)
        self.name = table.name
        self.table = table
        data = self.table.get('*')
        self.data = data
        self.rows = {}
        self.create_rows(len(data))   
        self.set_dataset(data)        
        self.add_scrollbar()
        self.packfill()
    
    def config_row(self, i):
        entry, text = self.rows[i]
        p = self.data[i]

        if len(p) >= 2:
           name, code = p[0:2]
        else:
           name = p
        entry.set_name(name)           
        #if len(code) > 500:
        #    code = code[0:500]
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
        entry = TextEntry(self, width=20, height=1)
        self.add(entry)
        text = TextEntry(self, width=110, height=1)
        self.add(text)
        self.rows[i] = (entry, text) 
        self.newline()
        
    def create_rows(self, row, col=2):        
        n = row + 3
        if n > 100:
            n = 100
        n = max(10, n)
        for i in range(n):            
            self.add_row(i)      
            

class dbTableView():
    def __init__(self, table):  
        self.table = table
        self.title = table.db.name + '.db - ' + table.name

    def show(self):       
        self.app = app = App(title=self.title, size=(1110, 800))      
        self.table_view = TableView(app, self.table)
        self.table_view.pack()
        app.mainloop() 
        

class dbView():
    def __init__(self, db, table=None):  
        self.db = db
        if table == None:
            table = db.get('tables')[0]
        self.table = table     
        self.title = db.name + '-' + table       
        
    def add_selector(self, app):
        from aui.dbSelector import dbSelector
        panel = dbSelector(app, self.db.name, self.table)
        return panel
        
    def add_editor(self, app):
        from aui.dbEditorFrame import dbEditorFrame     
        editor = dbEditorFrame(app) 
        editor.entry.config(width=48)
        return editor
        
    def show(self):       
        self.app = app = App(title=self.title, size=(1400, 900))      
        panel = self.add_selector(app)
        editor = self.add_editor(app)        
        panel.editor = editor
        editor.get_db_table = panel.get_db_table
        layout = app.get('layout') 
        layout.add_H2(panel, editor, 0.3)        
        app.mainloop()
        

if __name__ == '__main__':   
    import DB
    db = DB.open('code')
    if 0:
       #dbView(db).show()
       db.show()
    else:   
       dbTableView(DB.get_table('cache', 'cache')).show()
    

