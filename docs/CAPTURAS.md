# CAPTURAS — Guía para generar las 4 capturas del README

Captura cada pantalla con tu navegador (con la app corriendo en `http://localhost:5000`). Usa una ventana limpia (Ctrl+Shift+N en incógnito) y recorta con la herramienta de captura del sistema. Nombres sugeridos: `captura-reserva.png`, `captura-admin.png`, `captura-reportes.png`, `captura-mis-reservas.png`.

## 1. Formulario de reserva — `[CAPTURA: formulario de reserva]`

1. `python seed.py` y `python run.py`.
2. Abre `http://localhost:5000` en incógnito.
3. Elige un servicio, un empleado y una fecha con horario disponible.
4. Completa nombre, email y teléfono; pulsa **Reservar**.
5. Captura la pantalla de **confirmación de la reserva** con el código (ej. `RF-ABC123`).

## 2. Panel admin — `[CAPTURA: panel admin]`

1. Abre `http://localhost:5000/admin` en incógnito.
2. Inicia sesión con el usuario admin (credenciales de tus variables de entorno).
3. Captura el **Dashboard** (tarjetas de reservas hoy + accesos a Servicios/Empleados/Reservas).

## 3. Reportes con gráficos — `[CAPTURA: reportes con gráficos]`

1. En el panel admin, pulsa **Reportes** en la barra superior.
2. Genera antes unas reservas (al menos 2 servicios distintos y 1 cancelada) para que los gráficos y las métricas del mes se vean con datos.
3. Captura la pantalla completa con las 3 tarjetas del mes y los 2 gráficos (barras).

## 4. Mis reservas del cliente — `[CAPTURA: mis reservas del cliente]`

1. En incógnito, abre `http://localhost:5000/registrarse` y crea una cuenta con el email de una reserva previa (o regístrate y crea una reserva).
2. Pulsa **Mis reservas** en la barra superior.
3. Captura la lista con al menos una reserva y el botón de cancelar visible.