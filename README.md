# Gestión de banderillas coreanas

Aplicación de escritorio local hecha con Python, Tkinter y SQLite. No requiere instalar paquetes externos. La base activa se guarda fuera del proyecto, en `%USERPROFILE%\BanderillasCoreanas\banderillas.sqlite3`.

## Ejecutar en Windows

1. Instalar Python 3 desde python.org y marcar **Add Python to PATH** durante la instalación. Tkinter debe quedar incluido.
2. Abrir VS Code y elegir **Archivo > Abrir carpeta**; seleccionar `banderillas_app`.
3. Abrir una terminal en VS Code y ejecutar:

   ```powershell
   py app.py
   ```

La primera ejecución crea automáticamente la base de datos. Para cerrar, cerrar la ventana como cualquier aplicación.

## Uso sugerido

1. Cargar productos y luego ingredientes en las pestañas correspondientes.
2. Definir cada receta en **Recetas y producción**, usando los IDs visibles en las tablas.
3. Registrar compras y fabricar productos. La fabricación verifica ingredientes disponibles.
4. Abrir caja antes de operar. Registrar ventas con pagos separados por `;`, por ejemplo `Efectivo=1200;Transferencia=500`. Los pagos deben sumar exactamente el total de la venta.
5. Registrar gastos, egresos y retiros desde sus pestañas.
6. Consultar informes y generar respaldos periódicos.

Los campos de importes aceptan números decimales, por ejemplo `1250.50` (también `1250,50`). Las unidades de ingredientes son texto libre, por ejemplo `g`, `ml` o `unidad`.

## Reglas implementadas

- Importes almacenados en centavos enteros.
- Conexiones con claves foráneas, consultas parametrizadas y transacciones SQLite.
- Ventas con uno o más medios de pago, validación de suma y control de stock; cancelación trazable que repone producto.
- Producción con consumo de receta dentro de una operación atómica.
- Compras con costo promedio ponderado para ingredientes y productos terminados; cada venta conserva el costo unitario utilizado.
- Movimientos de compras, ventas, producción, ajustes y cancelaciones.
- Alertas de stock mínimo, gastos, apertura/cierre de caja e informes con exportación CSV separado por punto y coma y codificación compatible con Excel.
- Copia mediante la API de respaldo SQLite; antes de restaurar se valida la integridad y se crea una copia preventiva.

## Respaldo y restauración

Usar **Crear respaldo SQLite** desde la pestaña **Informes y copias** y guardar la copia en otra unidad o servicio seguro. Para restaurar, elegir la copia desde esa misma pestaña y confirmar. La aplicación conserva además una copia preventiva en la carpeta de datos antes del reemplazo. Cerrá cualquier otra instancia del programa antes de restaurar.

## Git

Inicializar Git desde VS Code en esta carpeta. `.gitignore` evita incluir bases locales y exports. No subir datos de ventas o clientes al repositorio.

## Alcance actual

La aplicación está pensada para una computadora y un usuario a la vez. La caja y los pagos están orientados a un cierre de caja sencillo; el resultado de informes es estimado y no reemplaza asesoramiento contable o fiscal. Los IDs se muestran para facilitar configurar recetas desde la interfaz. Antes de usar datos reales, cargar registros ficticios y practicar creación y restauración de una copia.
