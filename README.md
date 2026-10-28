# Gestión de Banderillas Coreanas

Sistema de gestión desarrollado en Python para administrar un emprendimiento de venta de banderillas coreanas desde una aplicación de escritorio.

Permite organizar los productos, controlar los ingredientes disponibles, registrar las ventas y los gastos, gestionar la caja y consultar los resultados del negocio desde una sola aplicación.

## Funcionalidades

- **Gestión de productos e ingredientes:** registrar productos terminados, materias primas y sus existencias.
- **Control de recetas:** definir los ingredientes y las cantidades necesarias para elaborar cada producto.
- **Producción:** registrar la fabricación de productos y descontar automáticamente los ingredientes utilizados.
- **Compras:** registrar la adquisición de materias primas y actualizar sus costos.
- **Ventas:** registrar ventas, controlar el stock y dividir los pagos entre distintos medios de cobro.
- **Caja:** gestionar aperturas, cierres, gastos, egresos y retiros de dinero.
- **Control de costos:** calcular costos de productos y conservar el costo registrado al momento de cada venta.
- **Informes:** consultar información del negocio y exportar datos a archivos CSV.
- **Copias de seguridad:** crear respaldos de la base de datos y restaurarlos cuando sea necesario.
- **Alertas de stock:** identificar ingredientes o productos que necesitan reposición.

## Tecnologías utilizadas

- Python
- Tkinter para la interfaz gráfica.
- SQLite para almacenar la información.
- CSV para exportar informes.

## Almacenamiento de datos

La aplicación guarda la información en una base de datos local, ubicada fuera de la carpeta del proyecto. Esto permite conservar los registros aunque se mueva o actualice el código de la aplicación.

Se recomienda realizar copias de seguridad periódicas y probar el sistema con datos ficticios antes de comenzar a utilizarlo en el negocio.

## Alcance del proyecto

Es una aplicación local diseñada para utilizarse en una computadora y por un usuario a la vez. Está orientada a facilitar la organización cotidiana del emprendimiento y el seguimiento de sus movimientos.

Los resultados económicos son estimaciones de gestión y no reemplazan la contabilidad profesional ni las obligaciones fiscales.

## Estado del proyecto

Primera versión funcional en desarrollo, con herramientas para administrar productos, ingredientes, producción, ventas, caja e informes.
