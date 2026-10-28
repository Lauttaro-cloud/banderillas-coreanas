"""Reglas del negocio. Cada operación compuesta se confirma en una transacción."""
from database.db import connect, now

METHODS = ("Efectivo", "Transferencia", "Mercado Pago", "Otro")

def cents(value):
    return int(round(float(value.replace(',', '.')) * 100))

def money(value):
    return f"${value/100:,.2f}"

def add_product(name, category, price, cost, minimum=0):
    with connect() as c:
        c.execute("INSERT INTO products(name,category,price,cost,min_stock) VALUES(?,?,?,?,?)", (name.strip(),category.strip(),cents(price),cents(cost),float(minimum)))

def add_ingredient(name, unit, quantity, minimum, cost):
    with connect() as c:
        cur=c.execute("INSERT INTO ingredients(name,unit,quantity,min_stock,unit_cost) VALUES(?,?,?,?,?)",(name.strip(),unit.strip(),float(quantity),float(minimum),cents(cost)))
        if float(quantity): c.execute("INSERT INTO inventory_moves(created_at,item_type,item_id,item_name,movement,quantity,unit_cost,reference) VALUES(?,?,?,?,?,?,?,?)",(now(),'INGREDIENT',cur.lastrowid,name,'COMPRA',float(quantity),cents(cost),'ALTA'))

def set_recipe(product_id, ingredient_id, quantity):
    with connect() as c:
        c.execute("INSERT INTO recipes VALUES(?,?,?) ON CONFLICT(product_id,ingredient_id) DO UPDATE SET quantity=excluded.quantity",(int(product_id),int(ingredient_id),float(quantity)))

def purchase(ingredient_id, quantity, total_cost):
    q=float(quantity); cost=cents(total_cost)
    if q<=0 or cost<0: raise ValueError('Cantidad o costo inválido.')
    with connect() as c:
        i=c.execute('SELECT * FROM ingredients WHERE id=?',(ingredient_id,)).fetchone()
        if not i: raise ValueError('Ingrediente inexistente.')
        avg=round((i['quantity']*i['unit_cost']+cost)/(i['quantity']+q))
        c.execute('UPDATE ingredients SET quantity=quantity+?,unit_cost=? WHERE id=?',(q,avg,ingredient_id))
        c.execute("INSERT INTO inventory_moves(created_at,item_type,item_id,item_name,movement,quantity,unit_cost,reference) VALUES(?,?,?,?,?,?,?,?)",(now(),'INGREDIENT',ingredient_id,i['name'],'COMPRA',q,round(cost/q),'Compra'))

def produce(product_id, quantity):
    q=float(quantity)
    if q<=0: raise ValueError('La cantidad debe ser mayor que cero.')
    with connect() as c:
        p=c.execute('SELECT * FROM products WHERE id=?',(product_id,)).fetchone()
        recipe=c.execute('SELECT r.quantity,i.* FROM recipes r JOIN ingredients i ON i.id=r.ingredient_id WHERE r.product_id=?',(product_id,)).fetchall()
        if not p or not recipe: raise ValueError('Producto inexistente o sin receta.')
        for i in recipe:
            need=i['quantity']*q
            avail=c.execute('SELECT quantity FROM ingredients WHERE id=?',(i['id'],)).fetchone()[0]
            if avail+1e-9<need: raise ValueError(f"Stock insuficiente de {i['name']}.")
        batch_cost=0
        for i in recipe:
            need=i['quantity']*q; batch_cost+=round(need*i['unit_cost'])
            c.execute('UPDATE ingredients SET quantity=quantity-? WHERE id=?',(need,i['id']))
            c.execute("INSERT INTO inventory_moves(created_at,item_type,item_id,item_name,movement,quantity,unit_cost,reference) VALUES(?,?,?,?,?,?,?,?)",(now(),'INGREDIENT',i['id'],i['name'],'PRODUCCION',-need,i['unit_cost'],p['name']))
        per_unit=round(batch_cost/q)
        # costo promedio ponderado del producto terminado
        newcost=round((p['stock']*p['cost']+batch_cost)/(p['stock']+q)) if p['stock']+q else per_unit
        c.execute('UPDATE products SET stock=stock+?,cost=? WHERE id=?',(q,newcost,product_id))
        c.execute("INSERT INTO inventory_moves(created_at,item_type,item_id,item_name,movement,quantity,unit_cost,reference) VALUES(?,?,?,?,?,?,?,?)",(now(),'PRODUCT',product_id,p['name'],'PRODUCCION',q,per_unit,'Producción'))

def sell(lines, payments, discount=0, note=''):
    # lines: [(product_id, qty, unit_price_override_or_None)], payment [(medio, pesos)]
    discount_c=cents(discount)
    if discount_c<0: raise ValueError('Descuento inválido.')
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        prepared=[]; subtotal=0; demand={}
        for pid,qty,override in lines:
            qty=float(qty)
            p=c.execute('SELECT * FROM products WHERE id=? AND active=1',(int(pid),)).fetchone()
            if not p or qty<=0: raise ValueError('Producto inactivo/inexistente o cantidad inválida.')
            demand[p['id']]=demand.get(p['id'],0)+qty
            unit=p['price'] if override in (None,'') else cents(override)
            if unit<0: raise ValueError('Precio inválido.')
            total=round(unit*qty); subtotal+=total; prepared.append((p,qty,unit,total))
        if not prepared: raise ValueError('Agregá al menos un producto.')
        for pid,qty in demand.items():
            p=c.execute('SELECT name,stock FROM products WHERE id=?',(pid,)).fetchone()
            if p['stock']+1e-9<qty: raise ValueError(f"Stock insuficiente de {p['name']}.")
        if discount_c>subtotal: raise ValueError('El descuento supera el subtotal.')
        total=subtotal-discount_c
        if any(method not in METHODS for method,_ in payments): raise ValueError('Medio inválido. Usá Efectivo, Transferencia, Mercado Pago u Otro.')
        paid=sum(cents(amount) for _,amount in payments if float(str(amount).replace(',','.'))>0)
        if paid!=total: raise ValueError(f"Los pagos deben sumar exactamente {money(total)}.")
        cur=c.execute("INSERT INTO sales(created_at,subtotal,discount,total,note) VALUES(?,?,?,?,?)",(now(),subtotal,discount_c,total,note))
        sid=cur.lastrowid
        for method,amount in payments:
            a=cents(amount)
            if a<0: raise ValueError('Pago inválido.')
            if a: c.execute('INSERT INTO payments(sale_id,method,amount) VALUES(?,?,?)',(sid,method,a))
        for p,qty,unit,line_total in prepared:
            c.execute('INSERT INTO sale_items(sale_id,product_id,product_name,quantity,unit_price,unit_cost,line_total) VALUES(?,?,?,?,?,?,?)',(sid,p['id'],p['name'],qty,unit,p['cost'],line_total))
            c.execute('UPDATE products SET stock=stock-? WHERE id=?',(qty,p['id']))
            c.execute("INSERT INTO inventory_moves(created_at,item_type,item_id,item_name,movement,quantity,unit_cost,reference) VALUES(?,?,?,?,?,?,?,?)",(now(),'PRODUCT',p['id'],p['name'],'VENTA',-qty,p['cost'],f'Venta {sid}'))
        return sid

def cancel_sale(sale_id, reason):
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        s=c.execute("SELECT * FROM sales WHERE id=? AND status='CONFIRMADA'",(sale_id,)).fetchone()
        if not s: raise ValueError('Venta inexistente o ya cancelada.')
        items=c.execute('SELECT * FROM sale_items WHERE sale_id=?',(sale_id,)).fetchall()
        for x in items:
            c.execute('UPDATE products SET stock=stock+? WHERE id=?',(x['quantity'],x['product_id']))
            c.execute("INSERT INTO inventory_moves(created_at,item_type,item_id,item_name,movement,quantity,unit_cost,reference,note) VALUES(?,?,?,?,?,?,?,?,?)",(now(),'PRODUCT',x['product_id'],x['product_name'],'CANCELACION',x['quantity'],x['unit_cost'],f'Venta {sale_id}',reason))
        c.execute("UPDATE sales SET status='CANCELADA',note=note || ? WHERE id=?",(f' | Cancelación: {reason}',sale_id))

def add_expense(category, description, amount, method, date=None):
    with connect() as c:
        c.execute('INSERT INTO expenses(created_at,category,description,amount,method) VALUES(?,?,?,?,?)',(date or now(),category.strip(),description.strip(),cents(amount),method))

def inventory_change(item_type, item_id, movement, quantity, note=''):
    """Ajuste trazable de stock. Cantidad con signo; merma siempre reduce stock."""
    q=float(quantity)
    if q==0: raise ValueError('La cantidad debe ser distinta de cero.')
    if movement=='MERMA' and q>0: raise ValueError('Una merma debe ser una cantidad negativa.')
    table='products' if item_type=='PRODUCT' else 'ingredients'
    with connect() as c:
        item=c.execute(f'SELECT * FROM {table} WHERE id=?',(int(item_id),)).fetchone()
        if not item: raise ValueError('Artículo inexistente.')
        if item['stock' if item_type=='PRODUCT' else 'quantity']+q < -1e-9: raise ValueError('El movimiento dejaría stock negativo.')
        stock_col='stock' if item_type=='PRODUCT' else 'quantity'
        c.execute(f'UPDATE {table} SET {stock_col}={stock_col}+? WHERE id=?',(q,int(item_id)))
        c.execute('INSERT INTO inventory_moves(created_at,item_type,item_id,item_name,movement,quantity,unit_cost,reference,note) VALUES(?,?,?,?,?,?,?,?,?)',(now(),item_type,int(item_id),item['name'],movement,q,item['cost'] if item_type=='PRODUCT' else item['unit_cost'],movement,note))

def open_cash(balance, note=''):
    with connect() as c:
        if c.execute('SELECT 1 FROM cash_sessions WHERE closed_at IS NULL').fetchone(): raise ValueError('Ya hay una caja abierta.')
        c.execute('INSERT INTO cash_sessions(opened_at,opening_balance,note) VALUES(?,?,?)',(now(),cents(balance),note))

def cash_move(kind, amount, method='Efectivo', note=''):
    with connect() as c:
        s=c.execute('SELECT * FROM cash_sessions WHERE closed_at IS NULL ORDER BY id DESC LIMIT 1').fetchone()
        if not s: raise ValueError('Primero abrí la caja.')
        c.execute('INSERT INTO cash_moves(session_id,created_at,kind,amount,method,note) VALUES(?,?,?,?,?,?)',(s['id'],now(),kind,cents(amount),method,note))

def close_cash(counted, note=''):
    with connect() as c:
        s=c.execute('SELECT * FROM cash_sessions WHERE closed_at IS NULL ORDER BY id DESC LIMIT 1').fetchone()
        if not s: raise ValueError('No hay caja abierta.')
        expected=s['opening_balance']
        rows=c.execute('SELECT kind,amount FROM cash_moves WHERE session_id=?',(s['id'],)).fetchall()
        for r in rows: expected += r['amount'] if r['kind']=='INGRESO' else -r['amount']
        # Ventas y gastos en efectivo ocurridos desde apertura
        for p in c.execute("SELECT p.amount FROM payments p JOIN sales s ON s.id=p.sale_id WHERE s.status='CONFIRMADA' AND p.method='Efectivo' AND s.created_at>=?",(s['opened_at'],)): expected+=p['amount']
        for e in c.execute("SELECT amount FROM expenses WHERE method='Efectivo' AND created_at>=?",(s['opened_at'],)): expected-=e['amount']
        c.execute('UPDATE cash_sessions SET closed_at=?,expected_balance=?,counted_balance=?,note=note || ? WHERE id=?',(now(),expected,cents(counted),f' | {note}' if note else '',s['id']))
        return expected

