# SPEC.md — ReservaFácil

Sistema web de reservas para una peluquería local en Lima, Perú.
Requisitos funcionales en notación **EARS** (Easy Approach to Requirements Syntax):
`Cuando <disparador>, el sistema deberá <respuesta> [según <condición>].`

Convenciones de nomenclatura en este documento:
- **RF-SYS** = requisitos de sistema (validación, reglas de negocio).
- **RF-CLI** = requisitos del actor Cliente.
- **RF-ADM** = requisitos del actor Administrador.

---

## 1. Actor Cliente

### 1.1 Ver disponibilidad

- **RF-CLI-01** — Cuando el cliente acceda a la página de inicio, el sistema deberá mostrar el catálogo de servicios disponibles.
- **RF-CLI-02** — Cuando el cliente seleccione un servicio, el sistema deberá mostrar los empleados capaces de realizarlo y sus horarios disponibles.
- **RF-CLI-03** — Cuando el cliente consulte una fecha, el sistema deberá mostrar solo los horarios libres, según la regla de no-overbooking (RF-SYS-03).

### 1.2 Crear reserva

- **RF-CLI-04** — Cuando el cliente envíe el formulario de reserva con datos válidos, el sistema deberá crear una reserva con estado "confirmada" y generar un ID único por reserva (RF-SYS-05).
- **RF-CLI-05** — Cuando el cliente envíe el formulario de reserva con datos inválidos o incompletos, el sistema deberá rechazar la creación y mostrar mensajes de error claros.
- **RF-CLI-06** — Cuando el cliente envíe una reserva que se solape con una existente, el sistema deberá rechazarla según RF-SYS-02.
- **RF-CLI-07** — Cuando el cliente cree una reserva exitosamente, el sistema deberá mostrar una confirmación en pantalla y registrar un email simulado (RF-SYS-06).

### 1.3 Cancelar reserva

- **RF-CLI-08** — Cuando el cliente solicite cancelar su propia reserva, el sistema deberá cambiar su estado a "cancelada" y liberar el horario.
- **RF-CLI-09** — Cuando el cliente intente cancelar una reserva ajena o inexistente, el sistema deberá denegar la operación.

### 1.4 Ver sus reservas

- **RF-CLI-10** — Cuando el cliente consulte "mis reservas", el sistema deberá listar todas sus reservas con estado, fecha y servicio.
- **RF-CLI-11** — Cuando el cliente no tenga reservas, el sistema deberá mostrar un mensaje vacío orientativo.

---

## 2. Actor Administrador

### 2.1 Servicios (CRUD)

- **RF-ADM-01** — Cuando el administrador cree un servicio con nombre, precio y duración válidos, el sistema deberá guardarlo y permitir asignarlo a empleados.
- **RF-ADM-02** — Cuando el administrador edite un servicio existente, el sistema deberá persistir los cambios y reflejarlos en nuevas reservas.
- **RF-ADM-03** — Cuando el administrador elimine un servicio, el sistema deberá eliminarlo salvo que tenga reservas activas; en ese caso deberá rechazar la eliminación con aviso.

### 2.2 Empleados (CRUD)

- **RF-ADM-04** — Cuando el administrador cree un empleado con nombre y rol válidos, el sistema deberá guardarlo.
- **RF-ADM-05** — Cuando el administrador edite un empleado, el sistema deberá persistir los cambios.
- **RF-ADM-06** — Cuando el administrador elimine un empleado, el sistema deberá rechazarlo si tiene reservas activas; de lo contrario deberá eliminarlo.

### 2.3 Horarios de atención

- **RF-ADM-07** — Cuando el administrador defina el horario de atención (apertura/cierre por día), el sistema deberá aplicarlo al cálculo de disponibilidad.
- **RF-ADM-08** — Cuando el administrador asigne servicios a un empleado, el sistema deberá validar que el empleado exista.

### 2.4 Ver todas las reservas

- **RF-ADM-09** — Cuando el administrador acceda al panel, el sistema deberá listar todas las reservas con filtros por fecha, estado y empleado.
- **RF-ADM-10** — Cuando el administrador cancele una reserva, el sistema deberá cambiar su estado a "cancelada".

### 2.5 Reportes e inteligencia de negocio

- **RF-ADM-11** — Cuando el administrador acceda a reportes, el sistema deberá mostrar las métricas del mes (ingresos proyectados, tasa de cancelación y total de reservas) y gráficos de reservas por día (últimos 30 días) y de top de servicios, agrupado todo en zona horaria America/Lima.
- **RF-ADM-12** — Cuando el administrador solicite la exportación, el sistema deberá generar un CSV de reservas (UTF-8 con BOM, columnas `codigo, cliente_nombre, cliente_email, servicio, empleado, inicio, fin, estado, precio`) ordenado por fecha de inicio descendente, con filtros opcionales por `estado`, `desde` y `hasta` (YYYY-MM-DD).

---

## 3. Sistema

### 3.1 Validación de solapamientos

- **RF-SYS-01** — Cuando se registre una nueva reserva, el sistema deberá validar que no exista otra reserva "confirmada" del mismo empleado cuyo intervalo de tiempo se solape, según la duración del servicio.

### 3.2 Regla de no-overbooking

- **RF-SYS-02** — Cuando se registre una nueva reserva, el sistema deberá validar que el empleado no supere su capacidad de 1 cliente a la vez (sin reservas paralelas).
- **RF-SYS-03** — Cuando se calcule disponibilidad, el sistema deberá marcar como "no disponible" todo slot cuya reserva violaría RF-SYS-01 o RF-SYS-02.
- **RF-SYS-04** — Cuando se registre una reserva, el sistema deberá verificar que la fecha y la hora estén dentro del horario de atención (RF-ADM-07).

### 3.3 ID único por reserva

- **RF-SYS-05** — Cuando se cree una reserva, el sistema deberá generar un ID único (código legible, p. ej. `RF-XXXXXX`), colision-free, independiente del ID de base de datos.

### 3.4 Email simulado

- **RF-SYS-06** — Cuando se cree o cancele una reserva, el sistema deberá emitir un email simulado por `logger`/consola (prohibido usar APIs de email reales).
- **RF-SYS-07** — Cuando se cree, cancele, confirme o complete una reserva y el cliente tenga teléfono registrado, el sistema deberá emitir una notificación de WhatsApp simulada (consola + `instance/whatsapp.log`), siguiendo el patrón del email simulado (RF-SYS-06).
