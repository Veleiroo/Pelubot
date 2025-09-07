# ---------------------------------------------
# Menú CLI para interacción con el asistente
# ---------------------------------------------

# Este archivo contiene funciones para mostrar el menú de la aplicación en consola
# y gestionar la interacción básica con el usuario.

from __future__ import annotations
import sys
from datetime import datetime, date, time, timedelta
from typing import Optional, List
from data import SERVICES, PROS, SERVICE_BY_ID, PRO_BY_ID, RESERVATIONS
from models import Reservation, RescheduleIn
from logic import (
    parse_date, parse_time, find_available_slots,
    find_reservation, cancel_reservation, apply_reschedule
)

# ------------------------
# Helpers de entrada
# ------------------------
def ask(prompt: str) -> str:
    """
    Solicita entrada al usuario por consola.
    """
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSaliendo…")
        sys.exit(0)

def choose_index(options: List[str], title: str = "Elige una opción") -> Optional[int]:
    """
    Muestra una lista de opciones y solicita al usuario elegir una por número.
    """
    if not options:
        print("No hay opciones.")
        return None
    print(f"\n{title}:")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        s = ask("Número: ")
        if not s:
            return None
        if s.isdigit():
            idx = int(s)
            if 1 <= idx <= len(options):
                return idx - 1
        print("→ Introduce un número válido.")

def input_date() -> Optional[date]:
    """
    Solicita una fecha al usuario en formato válido.
    """
    print("\nFecha (formato YYYY-MM-DD o DD/MM, Enter para cancelar)")
    while True:
        s = ask("> ")
        if not s:
            return None
        d = parse_date(s)
        if d:
            return d
        print("→ Formato no válido. Ej.: 2025-09-05 o 05/09")

def input_time() -> Optional[time]:
    """
    Solicita una hora al usuario en formato válido.
    """
    print("\nHora (formato HH:MM 24h, Enter para cancelar)")
    while True:
        s = ask("> ")
        if not s:
            return None
        t = parse_time(s)
        if t:
            return t
        print("→ Formato no válido. Ej.: 17:30")

# ------------------------
# Acciones
# ------------------------
def action_list_services() -> Optional[str]:
    """
    Muestra los servicios disponibles y permite elegir uno.
    """
    options = [f"{s.name} ({s.duration_min} min, {s.price_eur:.2f}€)" for s in SERVICES]
    idx = choose_index(options, "Servicios")
    if idx is None:
        return None
    return SERVICES[idx].id

def action_choose_professional(service_id: str) -> Optional[str]:
    """
    Muestra los profesionales disponibles para un servicio y permite elegir uno.
    """
    avail = [p for p in PROS if service_id in p.services]
    if not avail:
        print("No hay profesionales para ese servicio.")
        return None
    options = [f"{p.name} (id: {p.id})" for p in avail]
    idx = choose_index(options, "Profesionales")
    if idx is None:
        return None
    return avail[idx].id

def action_show_slots(service_id: str, d: date, pro_id: Optional[str]) -> List[datetime]:
    """
    Muestra los huecos disponibles para un servicio y profesional en una fecha dada.
    """
    slots = find_available_slots(service_id, d, pro_id)
    if not slots:
        print("No hay huecos disponibles ese día.")
        return []
    # Mostramos como HH:MM
    print("\nHuecos disponibles:")
    for i, dt in enumerate(slots[:20], 1):  # mostramos hasta 20 para no saturar
        print(f"  {i}. {dt.strftime('%H:%M')} ({dt.isoformat()})")
    return slots

def action_book():
    """
    Gestiona el proceso de reserva de un servicio.
    """
    # Servicio
    srv_id = action_list_services()
    if not srv_id:
        return

    # Fecha
    d = input_date()
    if not d:
        return

    # Profesional (opcional)
    print("\n¿Elegir profesional? (Enter para autoasignar)")
    pro_id = action_choose_professional(srv_id)
    # Si el usuario pulsa Enter en el prompt de número, pro_id será None → autoasignaremos

    # Slots
    slots = action_show_slots(srv_id, d, pro_id)
    if not slots:
        return
    idx = choose_index([s.strftime("%H:%M") for s in slots], "Elige una hora")
    if idx is None:
        return
    start_dt = slots[idx]
    service = SERVICE_BY_ID[srv_id]

    # calculamos end_dt correctamente:
    end_dt = start_dt + timedelta(minutes=service.duration_min)

    # Si no se eligió pro, autoasignamos el primero que esté libre en ese slot
    chosen_pro = pro_id
    if not chosen_pro:
        for p in PROS:
            if srv_id not in p.services:
                continue
            # comprobamos solapado: reutilizamos find_available_slots para ese pro
            if start_dt in find_available_slots(srv_id, d, p.id):
                chosen_pro = p.id
                break
    if not chosen_pro:
        print("No hay profesional disponible a esa hora.")
        return

    # Crear reserva en memoria
    res_id = f"res_{len(RESERVATIONS) + 1}"
    reservation = Reservation(
        id=res_id,
        service_id=srv_id,
        professional_id=chosen_pro,
        start=start_dt,
        end=end_dt,
    )
    RESERVATIONS.append(reservation)

    print("\n✅ Reserva confirmada")
    print(f"ID: {reservation.id}")
    print(f"Servicio: {SERVICE_BY_ID[reservation.service_id].name}")
    print(f"Profesional: {PRO_BY_ID[reservation.professional_id].name}")
    print(f"Fecha/hora: {reservation.start.strftime('%Y-%m-%d %H:%M')} ({service.duration_min} min)")

def action_list_reservations():
    """
    Muestra las reservas actuales.
    """
    if not RESERVATIONS:
        print("\nNo hay reservas.")
        return
    print("\nReservas:")
    for r in RESERVATIONS:
        print(f"- {r.id}: {SERVICE_BY_ID[r.service_id].name} con {PRO_BY_ID[r.professional_id].name} "
              f"el {r.start.strftime('%Y-%m-%d %H:%M')} → {r.end.strftime('%H:%M')}")

def action_cancel():
    """
    Cancela una reserva existente.
    """
    if not RESERVATIONS:
        print("\nNo hay reservas para cancelar.")
        return
    ids = [r.id for r in RESERVATIONS]
    idx = choose_index(ids, "Elige ID de reserva a cancelar")
    if idx is None:
        return
    rid = ids[idx]
    ok = cancel_reservation(rid)
    print("\n" + ("✅ Cancelada" if ok else "❌ No se pudo cancelar"))

def action_reschedule():
    """
    Reprograma una reserva existente.
    """
    if not RESERVATIONS:
        print("\nNo hay reservas para reprogramar.")
        return
    ids = [r.id for r in RESERVATIONS]
    idx = choose_index(ids, "Elige ID de reserva a reprogramar")
    if idx is None:
        return
    rid = ids[idx]

    print("\nNueva fecha (Enter para mantener):")
    sdate = ask("> ")
    new_date = None
    if sdate:
        new_date_parsed = parse_date(sdate)
        if not new_date_parsed:
            print("→ Fecha inválida.")
            return
        new_date = new_date_parsed.isoformat()

    print("\nNueva hora (HH:MM, Enter para mantener):")
    stime = ask("> ")
    new_time = None
    if stime:
        new_time_parsed = parse_time(stime)
        if not new_time_parsed:
            print("→ Hora inválida.")
            return
        new_time = new_time_parsed.strftime("%H:%M")

    print("\nCambiar de profesional (Enter para mantener)? IDs disponibles:")
    print(", ".join([p.id for p in PROS]))
    sprof = ask("> ").strip() or None
    if sprof and sprof not in PRO_BY_ID:
        print("→ professional_id no existe.")
        return

    ok, msg, r = apply_reschedule(RescheduleIn(
        reservation_id=rid,
        new_date=new_date,
        new_time=new_time,
        professional_id=sprof
    ))
    if not ok:
        print(f"\n❌ {msg}")
        # si falla, sugerimos huecos
        r0 = find_reservation(rid)
        if r0:
            from logic import parse_date as _pd  # para seguridad si new_date es None
            d = _pd(new_date) if new_date else r0.start.date()
            pro = sprof or r0.professional_id
            if d and pro:
                print("Sugerencias:")
                alts = find_available_slots(r0.service_id, d, pro)
                if not alts:
                    print("  (sin huecos)")
                else:
                    for dt in alts[:5]:
                        print(" ", dt.strftime("%Y-%m-%d %H:%M"))
        return
    print("\n✅", msg)
    print(f"ID: {r.id} → {r.start.strftime('%Y-%m-%d %H:%M')}")

# ------------------------
# Menú principal
# ------------------------
def main():
    """
    Función principal que ejecuta el menú en bucle.
    """
    while True:
        print("\n=== Menú PeluBot (CLI) ===")
        print("1) Reservar")
        print("2) Ver reservas")
        print("3) Cancelar reserva")
        print("4) Reprogramar")
        print("5) Salir")
        choice = ask("> ")
        if choice == "1":
            action_book()
        elif choice == "2":
            action_list_reservations()
        elif choice == "3":
            action_cancel()
        elif choice == "4":
            action_reschedule()
        elif choice == "5":
            print("¡Hasta luego!")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    main()
