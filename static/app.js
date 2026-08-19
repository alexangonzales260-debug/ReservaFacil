"use strict";

const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

const servicioSel = document.getElementById('servicio');
const empleadoSel = document.getElementById('empleado');
const fechaInput = document.getElementById('fecha');
const estadoDisp = document.getElementById('estado-disponibilidad');
const seccionSlots = document.getElementById('seccion-slots');
const gridSlots = document.getElementById('grid-slots');
const seccionForm = document.getElementById('seccion-form');
const resumenSlot = document.getElementById('resumen-slot');
const btnReservar = document.getElementById('btn-reservar');
const errorForm = document.getElementById('error-form');
const seccionConfirmacion = document.getElementById('seccion-confirmacion');
const codigoReserva = document.getElementById('codigo-reserva');
const detalleConfirmacion = document.getElementById('detalle-confirmacion');
const linkDetalle = document.getElementById('link-detalle');

let servicios = [];
let empleados = [];
let slotSeleccionado = null;

const hoy = new Date();
const isoHoy = hoy.toISOString().slice(0, 10);
fechaInput.value = isoHoy;
fechaInput.min = isoHoy;

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Error en la solicitud');
  return data;
}

function formatearFechaHora(fechaISO, hora) {
  const [y, m, d] = fechaISO.split('-');
  return `${d}/${m}/${y} ${hora}`;
}

function cargarCatalogo() {
  Promise.all([
    fetchJSON('/api/v1/servicios'),
    fetchJSON('/api/v1/empleados')
  ]).then(([dataServ, dataEmp]) => {
    servicios = dataServ.servicios;
    empleados = dataEmp.empleados;
    servicios.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = `${s.nombre} · ${s.duracion_minutos} min · S/ ${Number(s.precio).toFixed(2)}`;
      servicioSel.appendChild(opt);
    });
    empleados.forEach(e => {
      const opt = document.createElement('option');
      opt.value = e.id;
      opt.textContent = `${e.nombre} (${e.horario_inicio}–${e.horario_fin})`;
      empleadoSel.appendChild(opt);
    });
    if (!servicios.length) {
      estadoDisp.textContent = 'Aún no hay servicios registrados.';
    }
  }).catch(err => {
    estadoDisp.textContent = 'No se pudo cargar el catálogo: ' + err.message;
  });
}

function seleccionarSlot(slot) {
  slotSeleccionado = slot;
  const serv = servicios.find(s => s.id === Number(servicioSel.value));
  const emp = empleados.find(e => e.id === Number(empleadoSel.value));
  const partes = [
    emp ? emp.nombre : 'Empleado',
    formatearFechaHora(fechaInput.value, slot),
    serv ? serv.nombre : ''
  ];
  resumenSlot.textContent = partes.filter(Boolean).join(' · ');
  seccionForm.classList.remove('hidden');
  errorForm.classList.add('hidden');
  seccionForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function cargarDisponibilidad() {
  seccionForm.classList.add('hidden');
  seccionConfirmacion.classList.add('hidden');
  slotSeleccionado = null;
  gridSlots.innerHTML = '';

  if (!empleadoSel.value || !fechaInput.value) {
    seccionSlots.classList.add('hidden');
    estadoDisp.textContent = 'Selecciona un empleado y una fecha para ver horarios.';
    return;
  }

  seccionSlots.classList.remove('hidden');
  estadoDisp.textContent = 'Cargando horarios…';

  const url = `/api/v1/empleados/${empleadoSel.value}/disponibilidad?fecha=${fechaInput.value}`;
  fetchJSON(url)
    .then(data => {
      gridSlots.innerHTML = '';
      if (!data.slots.length) {
        estadoDisp.textContent = 'No hay horarios disponibles para esa fecha.';
        return;
      }
      data.slots.forEach(slot => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = slot;
        btn.className = 'bg-green-500 hover:bg-green-600 text-white rounded-lg py-2 text-sm font-medium transition-colors';
        btn.addEventListener('click', () => seleccionarSlot(slot));
        gridSlots.appendChild(btn);
      });
      estadoDisp.textContent = `Horarios disponibles para ${fechaInput.value}:`;
    })
    .catch(err => {
      estadoDisp.textContent = 'Error al cargar disponibilidad: ' + err.message;
    });
}

btnReservar.addEventListener('click', async () => {
  errorForm.classList.add('hidden');
  const nombre = document.getElementById('nombre').value.trim();
  const email = document.getElementById('email').value.trim();
  const telefono = document.getElementById('telefono').value.trim();
  const notas = document.getElementById('notas').value.trim();

  if (!nombre || !email) {
    errorForm.textContent = 'Por favor completa tu nombre y email.';
    errorForm.classList.remove('hidden');
    return;
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    errorForm.textContent = 'Ingresa un email válido.';
    errorForm.classList.remove('hidden');
    return;
  }

  btnReservar.disabled = true;
  const payload = {
    servicio_id: Number(servicioSel.value),
    empleado_id: Number(empleadoSel.value),
    fecha_hora_inicio: `${fechaInput.value}T${slotSeleccionado}`,
    nombre,
    email,
    telefono,
    notas
  };
  try {
    const data = await fetchJSON('/api/v1/reservas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify(payload)
    });
    const serv = servicios.find(s => s.id === Number(data.servicio_id));
    const emp = empleados.find(e => e.id === Number(data.empleado_id));
    codigoReserva.textContent = data.codigo;
    detalleConfirmacion.textContent = [
      serv ? serv.nombre : '',
      emp ? emp.nombre : '',
      formatearFechaHora(fechaInput.value, slotSeleccionado)
    ].filter(Boolean).join(' · ');
    linkDetalle.href = `/reservas/${data.codigo}`;
    seccionForm.classList.add('hidden');
    seccionSlots.classList.add('hidden');
    seccionConfirmacion.classList.remove('hidden');
    seccionConfirmacion.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } catch (err) {
    errorForm.textContent = 'No se pudo crear la reserva: ' + err.message;
    errorForm.classList.remove('hidden');
  } finally {
    btnReservar.disabled = false;
  }
});

document.getElementById('btn-nueva').addEventListener('click', () => window.location.reload());
empleadoSel.addEventListener('change', cargarDisponibilidad);
fechaInput.addEventListener('change', cargarDisponibilidad);

cargarCatalogo();