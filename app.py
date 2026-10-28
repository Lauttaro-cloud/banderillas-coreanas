"""Gestión local de un emprendimiento de banderillas coreanas. Requiere solo Python."""
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from database import db
from services import operations as op

def rows(sql, args=()):
    with db.connect() as c: return c.execute(sql,args).fetchall()

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Banderillas coreanas | Gestión'); self.geometry('1120x720'); self.minsize(900,600)
        db.initialize()
        self.tabs=ttk.Notebook(self); self.tabs.pack(fill='both',expand=True,padx=10,pady=10)
        self.home=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.home,text='Inicio'); self.make_home()
        self.make_products(); self.make_ingredients(); self.make_recipe_production(); self.make_sales(); self.make_expenses(); self.make_cash(); self.make_reports()
        self.refresh_all()

    def form(self,parent,fields):
        box=ttk.LabelFrame(parent,text='Datos',padding=8); box.pack(side='left',fill='y',padx=(0,10),pady=4)
        entries={}
        for r,(key,label) in enumerate(fields):
            ttk.Label(box,text=label).grid(row=r,column=0,sticky='w',pady=3)
            e=ttk.Entry(box,width=25); e.grid(row=r,column=1,pady=3,padx=5); entries[key]=e
        return entries
    def table(self,parent,columns,headings):
        wrap=ttk.Frame(parent); wrap.pack(side='left',fill='both',expand=True,pady=4)
        tree=ttk.Treeview(wrap,columns=columns,show='headings',height=15)
        for col,title in zip(columns,headings): tree.heading(col,text=title); tree.column(col,width=105,anchor='w')
        sy=ttk.Scrollbar(wrap,orient='vertical',command=tree.yview); tree.configure(yscrollcommand=sy.set)
        tree.pack(side='left',fill='both',expand=True); sy.pack(side='right',fill='y')
        return tree
    def add_tab(self,title):
        frame=ttk.Frame(self.tabs,padding=10); self.tabs.add(frame,text=title); return frame
    def button(self,parent,label,fn):
        row=parent.grid_size()[1]
        ttk.Button(parent,text=label,command=lambda:self.safe(fn)).grid(row=row,column=0,columnspan=2,sticky='ew',pady=3)
    def safe(self,fn):
        try: fn(); self.refresh_all()
        except Exception as e: messagebox.showerror('No se pudo completar',str(e),parent=self)
    def val(self,entries,key): return entries[key].get().strip()
    def clear(self,entries):
        for e in entries.values(): e.delete(0,'end')
    def fill_tree(self,tree,data):
        tree.delete(*tree.get_children())
        for row in data: tree.insert('', 'end', values=tuple(row))

    def make_home(self):
        ttk.Label(self.home,text='Panel del emprendimiento',font=('Segoe UI',20,'bold')).pack(anchor='w')
        self.home_info=ttk.Label(self.home,font=('Segoe UI',12),justify='left'); self.home_info.pack(anchor='w',pady=18)
        ttk.Label(self.home,text='Los importes se guardan en centavos. Los costos de ingredientes usan promedio ponderado; el costo aplicado queda guardado en cada venta.',wraplength=850).pack(anchor='w',pady=10)
    def make_products(self):
        f=self.add_tab('Productos'); self.pe=self.form(f,[('name','Nombre'),('category','Categoría'),('price','Precio de venta ($)'),('cost','Costo actual ($)'),('min','Stock mínimo')]); self.pt=self.table(f,('id','name','category','price','cost','stock','min','active'),('ID','Producto','Categoría','Precio','Costo','Stock','Mínimo','Activo'))
        bar=ttk.Frame(self.pe['name'].master); bar.grid(row=8,column=0,columnspan=2,sticky='ew',pady=8)
        ttk.Button(bar,text='Agregar',command=lambda:self.safe(self.save_product)).pack(fill='x',pady=2); ttk.Button(bar,text='Guardar cambios del seleccionado',command=lambda:self.safe(self.edit_product)).pack(fill='x',pady=2); ttk.Button(bar,text='Activar / desactivar',command=lambda:self.safe(self.toggle_product)).pack(fill='x',pady=2)
        self.pmove=self.form(f,[('qty','Cantidad (+/-)'),('note','Motivo')]); self.button(self.pmove['qty'].master,'Ajustar stock de producto',self.adjust_product); self.button(self.pmove['qty'].master,'Registrar merma de producto',self.waste_product)
        self.pt.bind('<<TreeviewSelect>>',self.select_product)
    def select_product(self,event=None):
        sel=self.pt.selection()
        if not sel:return
        v=self.pt.item(sel[0],'values'); self.clear(self.pe)
        vals={'name':v[1],'category':v[2],'price':str(float(v[3].replace('$','').replace(',',''))),'cost':str(float(v[4].replace('$','').replace(',',''))),'min':v[6]}
        for k,x in vals.items():self.pe[k].insert(0,x)
    def save_product(self):
        op.add_product(self.val(self.pe,'name'),self.val(self.pe,'category'),self.val(self.pe,'price'),self.val(self.pe,'cost'),self.val(self.pe,'min') or 0); self.clear(self.pe)
    def edit_product(self):
        sel=self.pt.selection()
        if not sel:raise ValueError('Seleccioná un producto.')
        v=self.pt.item(sel[0],'values')
        with db.connect() as c:c.execute('UPDATE products SET name=?,category=?,price=?,cost=?,min_stock=? WHERE id=?',(self.val(self.pe,'name'),self.val(self.pe,'category'),op.cents(self.val(self.pe,'price')),op.cents(self.val(self.pe,'cost')),float(self.val(self.pe,'min') or 0),int(v[0])))
    def toggle_product(self):
        sel=self.pt.selection()
        if not sel:raise ValueError('Seleccioná un producto.')
        v=self.pt.item(sel[0],'values')
        with db.connect() as c:c.execute('UPDATE products SET active=1-active WHERE id=?',(int(v[0]),))
    def adjust_product(self):
        op.inventory_change('PRODUCT',self.selected_id(self.pt),'AJUSTE',self.val(self.pmove,'qty'),self.val(self.pmove,'note')); self.clear(self.pmove)
    def waste_product(self):
        q=-abs(float(self.val(self.pmove,'qty'))); op.inventory_change('PRODUCT',self.selected_id(self.pt),'MERMA',q,self.val(self.pmove,'note')); self.clear(self.pmove)

    def make_ingredients(self):
        f=self.add_tab('Ingredientes y stock'); self.ie=self.form(f,[('name','Ingrediente'),('unit','Unidad (g, ml, unidad)'),('quantity','Cantidad inicial'),('min','Stock mínimo'),('cost','Costo por unidad ($)')]); self.it=self.table(f,('id','name','unit','qty','min','cost'),('ID','Ingrediente','Unidad','Disponible','Mínimo','Costo/u'))
        b=ttk.Frame(self.ie['name'].master); b.grid(row=6,column=0,columnspan=2,sticky='ew',pady=5)
        ttk.Button(b,text='Agregar ingrediente',command=lambda:self.safe(self.save_ingredient)).pack(fill='x',pady=2); ttk.Button(b,text='Registrar compra',command=lambda:self.safe(self.purchase)).pack(fill='x',pady=2); ttk.Button(b,text='Ajustar stock',command=lambda:self.safe(self.adjust_ingredient)).pack(fill='x',pady=2)
        ttk.Button(b,text='Registrar merma',command=lambda:self.safe(self.waste_ingredient)).pack(fill='x',pady=2)
        self.imove=self.form(self.it.master,[('qty','Cantidad (+/-)'),('cost','Costo total compra ($)'),('note','Motivo')])
    def save_ingredient(self):
        q=float(self.val(self.ie,'quantity') or 0); op.add_ingredient(self.val(self.ie,'name'),self.val(self.ie,'unit'),q,float(self.val(self.ie,'min') or 0),self.val(self.ie,'cost') or 0); self.clear(self.ie)
    def selected_id(self,tree):
        s=tree.selection()
        if not s:raise ValueError('Seleccioná una fila en la tabla.')
        return int(tree.item(s[0],'values')[0])
    def purchase(self):
        iid=self.selected_id(self.it); e=self.imove
        op.purchase(iid,self.val(e,'qty'),self.val(e,'cost')); self.clear(e)
    def adjust_ingredient(self):
        iid=self.selected_id(self.it); q=float(self.val(self.imove,'qty')); n=self.val(self.imove,'note') or 'Ajuste manual'
        with db.connect() as c:
            i=c.execute('SELECT * FROM ingredients WHERE id=?',(iid,)).fetchone()
            if i['quantity']+q<0:raise ValueError('El ajuste dejaría stock negativo.')
            c.execute('UPDATE ingredients SET quantity=quantity+? WHERE id=?',(q,iid))
            c.execute('INSERT INTO inventory_moves(created_at,item_type,item_id,item_name,movement,quantity,unit_cost,reference,note) VALUES(?,?,?,?,?,?,?,?,?)',(db.now(),'INGREDIENT',iid,i['name'],'AJUSTE',q,i['unit_cost'],'Manual',n))
    def waste_ingredient(self):
        q=-abs(float(self.val(self.imove,'qty'))); op.inventory_change('INGREDIENT',self.selected_id(self.it),'MERMA',q,self.val(self.imove,'note')); self.clear(self.imove)

    def make_recipe_production(self):
        f=self.add_tab('Recetas y producción'); self.re=self.form(f,[('product','ID producto'),('ingredient','ID ingrediente'),('qty','Cantidad por unidad')]); self.button(self.re['product'].master,'Guardar ingrediente en receta',self.recipe)
        self.prod=self.form(f,[('product','ID producto a fabricar'),('qty','Unidades a fabricar')]); self.button(self.prod['product'].master,'Registrar producción',self.production)
        self.rt=self.table(f,('product','ingredient','qty'),('Producto','Ingrediente','Cant. por unidad'))
        ttk.Label(f,text='Usá los IDs visibles en Productos e Ingredientes. La producción actualiza costos y stocks automáticamente.').pack(anchor='w',pady=10)
    def recipe(self):
        op.set_recipe(self.val(self.re,'product'),self.val(self.re,'ingredient'),self.val(self.re,'qty')); self.clear(self.re)
    def production(self):
        op.produce(self.val(self.prod,'product'),self.val(self.prod,'qty')); self.clear(self.prod)

    def make_sales(self):
        f=self.add_tab('Ventas'); self.se=self.form(f,[('product','ID producto'),('qty','Cantidad'),('price','Precio unitario ($, vacío = lista)'),('discount','Descuento total ($)'),('payments','Pagos: Efectivo=100; Transferencia=20'),('note','Nota')]); self.button(self.se['product'].master,'Confirmar venta',self.sale)
        self.cancel=self.form(f,[('sale','ID venta a cancelar'),('reason','Motivo')]); self.button(self.cancel['sale'].master,'Cancelar venta y revertir stock',self.cancel_sale_ui)
        self.st=self.table(f,('id','date','total','status','items','payments'),('ID','Fecha','Total','Estado','Productos','Pagos'))
        ttk.Label(f,text='Ingresá pagos separados por punto y coma: Efectivo=100;Transferencia=50. Deben sumar el total exacto.').pack(anchor='w',pady=6)
    def sale(self):
        pays=[]
        for token in self.val(self.se,'payments').split(';'):
            if not token.strip():continue
            method,amount=token.split('=',1); pays.append((method.strip(),amount.strip()))
        override=self.val(self.se,'price') or None
        sid=op.sell([(int(self.val(self.se,'product')),float(self.val(self.se,'qty')),override)],pays,self.val(self.se,'discount') or 0,self.val(self.se,'note')); self.clear(self.se); messagebox.showinfo('Venta confirmada',f'Venta #{sid} registrada.',parent=self)
    def cancel_sale_ui(self):
        op.cancel_sale(self.val(self.cancel,'sale'),self.val(self.cancel,'reason')); self.clear(self.cancel)

    def make_expenses(self):
        f=self.add_tab('Gastos'); self.ee=self.form(f,[('category','Categoría'),('description','Descripción'),('amount','Importe ($)'),('method','Medio de pago'),('date','Fecha/hora (vacío = ahora)')]); self.button(self.ee['category'].master,'Registrar gasto',self.expense)
        self.et=self.table(f,('date','category','description','amount','method'),('Fecha','Categoría','Descripción','Importe','Medio'))
        ttk.Label(self.ee['category'].master,text='Medios: Efectivo, Transferencia, Mercado Pago u Otro').grid(row=8,column=0,columnspan=2,sticky='w')
    def expense(self):
        op.add_expense(self.val(self.ee,'category'),self.val(self.ee,'description'),self.val(self.ee,'amount'),self.val(self.ee,'method'),self.val(self.ee,'date') or None); self.clear(self.ee)

    def make_cash(self):
        f=self.add_tab('Caja y cierre'); self.ce=self.form(f,[('amount','Importe ($)'),('method','Medio de pago'),('note','Nota')]); self.button(self.ce['amount'].master,'Abrir caja (importe inicial)',self.open_cash)
        self.button(self.ce['amount'].master,'Registrar ingreso manual',lambda:op.cash_move('INGRESO',self.val(self.ce,'amount'),self.val(self.ce,'method') or 'Efectivo',self.val(self.ce,'note')))
        self.button(self.ce['amount'].master,'Registrar egreso / retiro',lambda:op.cash_move('EGRESO',self.val(self.ce,'amount'),self.val(self.ce,'method') or 'Efectivo',self.val(self.ce,'note')))
        self.button(self.ce['amount'].master,'Cerrar caja con conteo real',self.close_cash_ui)
        self.ct=self.table(f,('id','opened','closed','initial','expected','counted','difference'),('ID','Apertura','Cierre','Inicial','Esperado','Contado','Diferencia'))
    def open_cash(self):op.open_cash(self.val(self.ce,'amount'),self.val(self.ce,'note')); self.clear(self.ce)
    def close_cash_ui(self):
        expected=op.close_cash(self.val(self.ce,'amount'),self.val(self.ce,'note')); messagebox.showinfo('Caja cerrada',f'Saldo esperado: {op.money(expected)}\nContado: {self.val(self.ce,"amount")}',parent=self); self.clear(self.ce)

    def make_reports(self):
        f=self.add_tab('Informes y copias'); self.rf=self.form(f,[('from','Desde (AAAA-MM-DD)'),('to','Hasta (AAAA-MM-DD)')]); self.rf['from'].insert(0,date.today().replace(day=1).isoformat()); self.rf['to'].insert(0,date.today().isoformat())
        self.button(self.rf['from'].master,'Actualizar informe',self.report); self.button(self.rf['from'].master,'Exportar informe CSV',self.export_csv); self.button(self.rf['from'].master,'Crear respaldo SQLite',self.backup_ui); self.button(self.rf['from'].master,'Restaurar respaldo',self.restore_ui)
        self.report_text=tk.Text(f,height=13,width=70); self.report_text.pack(fill='both',expand=True,pady=8)
        self.alerts=self.table(f,('type','name','stock','minimum'),('Tipo','Artículo','Stock','Mínimo'))
        self.button(self.rf['from'].master,'Ver historial de inventario',self.inventory_history)
        self.ht=self.table(f,('date','type','name','movement','qty','reference'),('Fecha','Tipo','Artículo','Movimiento','Cantidad','Referencia'))
    def report_data(self):
        start=self.val(self.rf,'from')+'T00:00:00'; end=self.val(self.rf,'to')+'T23:59:59'
        sales=rows("SELECT s.id,s.created_at,s.total,s.status,group_concat(DISTINCT p.method) methods FROM sales s LEFT JOIN payments p ON p.sale_id=s.id WHERE s.created_at BETWEEN ? AND ? GROUP BY s.id ORDER BY s.id DESC",(start,end))
        expenses=rows('SELECT * FROM expenses WHERE created_at BETWEEN ? AND ? ORDER BY id DESC',(start,end))
        costs=rows("SELECT COALESCE(SUM(si.unit_cost*si.quantity),0) cost FROM sale_items si JOIN sales s ON s.id=si.sale_id WHERE s.status='CONFIRMADA' AND s.created_at BETWEEN ? AND ?",(start,end))[0]['cost']
        total=sum(s['total'] for s in sales if s['status']=='CONFIRMADA'); exp=sum(e['amount'] for e in expenses)
        return sales,expenses,costs,total,exp
    def report(self):
        sales,expenses,costs,total,exp=self.report_data()
        by=rows("SELECT p.method,SUM(p.amount) total FROM payments p JOIN sales s ON s.id=p.sale_id WHERE s.status='CONFIRMADA' AND s.created_at BETWEEN ? AND ? GROUP BY p.method",(self.val(self.rf,'from')+'T00:00:00',self.val(self.rf,'to')+'T23:59:59'))
        self.report_text.delete('1.0','end'); self.report_text.insert('end',f"Ventas confirmadas: {op.money(total)}\nCosto de productos vendidos: {op.money(costs)}\nGastos: {op.money(exp)}\nResultado estimado: {op.money(total-costs-exp)}\n\nCobros por medio:\n")
        for r in by:self.report_text.insert('end',f"  {r['method']}: {op.money(r['total'])}\n")
        self._csv_rows=[('VENTAS',s['id'],s['created_at'],s['total'],s['status'],s['methods']) for s in sales]+[('GASTO',e['id'],e['created_at'],e['amount'],e['category'],e['description']) for e in expenses]
    def export_csv(self):
        self.report(); path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='informe_banderillas.csv')
        if path:
            with open(path,'w',newline='',encoding='utf-8-sig') as out:
                w=csv.writer(out,delimiter=';'); w.writerow(['tipo','id','fecha','importe_centavos','estado_o_categoria','detalle']); w.writerows(self._csv_rows)
            messagebox.showinfo('Exportación lista',path,parent=self)
    def backup_ui(self):
        path=filedialog.asksaveasfilename(defaultextension='.sqlite3',filetypes=[('Base SQLite','*.sqlite3')],initialfile=f"respaldo_{date.today().isoformat()}.sqlite3")
        if path:db.backup(path); messagebox.showinfo('Respaldo creado',path,parent=self)
    def restore_ui(self):
        path=filedialog.askopenfilename(filetypes=[('Base SQLite','*.sqlite3'),('Todos','*.*')])
        if path and messagebox.askyesno('Confirmar restauración','Se reemplazará la base activa. Se guardará un respaldo preventivo. ¿Continuar?',parent=self):db.restore(path); self.refresh_all(); messagebox.showinfo('Restauración lista','La base fue restaurada.',parent=self)
    def inventory_history(self):
        self.fill_tree(self.ht,[(r['created_at'],r['item_type'],r['item_name'],r['movement'],r['quantity'],r['reference']) for r in rows('SELECT * FROM inventory_moves ORDER BY id DESC LIMIT 500')])

    def refresh_all(self):
        if not hasattr(self,'pt'):return
        self.fill_tree(self.pt,[(r['id'],r['name'],r['category'],op.money(r['price']),op.money(r['cost']),r['stock'],r['min_stock'],'Sí' if r['active'] else 'No') for r in rows('SELECT * FROM products ORDER BY name')])
        self.fill_tree(self.it,[(r['id'],r['name'],r['unit'],r['quantity'],r['min_stock'],op.money(r['unit_cost'])) for r in rows('SELECT * FROM ingredients ORDER BY name')])
        self.fill_tree(self.rt,[(r['product_name'],r['ingredient_name'],r['quantity']) for r in rows('SELECT p.name AS product_name,i.name AS ingredient_name,r.quantity FROM recipes r JOIN products p ON p.id=r.product_id JOIN ingredients i ON i.id=r.ingredient_id ORDER BY p.name,i.name')])
        self.fill_tree(self.st,[(s['id'],s['created_at'],op.money(s['total']),s['status'],s['items'] or '',s['methods'] or '') for s in rows("SELECT s.*, (SELECT group_concat(product_name || ' x' || quantity, ', ') FROM sale_items WHERE sale_id=s.id) items, (SELECT group_concat(DISTINCT method) FROM payments WHERE sale_id=s.id) methods FROM sales s ORDER BY s.id DESC LIMIT 300")])
        self.fill_tree(self.et,[(e['created_at'],e['category'],e['description'],op.money(e['amount']),e['method']) for e in rows('SELECT * FROM expenses ORDER BY id DESC LIMIT 300')])
        self.fill_tree(self.ct,[(s['id'],s['opened_at'],s['closed_at'] or 'ABIERTA',op.money(s['opening_balance']),op.money(s['expected_balance']) if s['expected_balance'] is not None else '',op.money(s['counted_balance']) if s['counted_balance'] is not None else '',op.money(s['counted_balance']-s['expected_balance']) if s['counted_balance'] is not None else '') for s in rows('SELECT * FROM cash_sessions ORDER BY id DESC LIMIT 100')])
        alerts=[('Ingrediente',r['name'],r['quantity'],r['min_stock']) for r in rows('SELECT * FROM ingredients WHERE quantity<=min_stock')]+[('Producto',r['name'],r['stock'],r['min_stock']) for r in rows('SELECT * FROM products WHERE active=1 AND stock<=min_stock')]
        self.fill_tree(self.alerts,alerts)
        self.home_info.config(text=f"Productos: {len(rows('SELECT id FROM products'))}    Ingredientes: {len(rows('SELECT id FROM ingredients'))}\nAlertas de stock: {len(alerts)}    Base de datos: {db.DB_PATH}")

if __name__=='__main__':
    App().mainloop()
