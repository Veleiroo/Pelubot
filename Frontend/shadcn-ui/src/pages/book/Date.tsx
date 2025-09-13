import { useLocation, useNavigate } from 'react-router-dom';
import { useBooking } from '@/store/booking';
import { useEffect, useMemo, useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { BookingSection } from '@/components/book/BookingSection';
import { BookingSteps } from '@/components/BookingSteps';
import { Card, CardContent } from '@/components/ui/card';
import { addDays, addMonths, endOfMonth, endOfWeek, format, isAfter, isBefore, isSameDay, isSameMonth, isToday, startOfMonth, startOfWeek, subMonths } from 'date-fns';
import { es } from 'date-fns/locale';
import { CalendarNav } from '@/components/ui/CalendarNav';
import '@/styles/calendar.css';

const toYmd = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
};

const ANY_PRO = '__any__';

const BookDate = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { serviceId, professionalId, slotStart, setProfessional, setDate, setSlot, setService } = useBooking((s) => ({
    serviceId: s.serviceId,
    professionalId: s.professionalId,
    slotStart: s.slotStart,
    setProfessional: s.setProfessional,
    setDate: s.setDate,
    setSlot: s.setSlot,
    setService: s.setService,
  }));
  const [selected, setSelected] = useState<Date | undefined>(undefined);
  const [month, setMonth] = useState<Date>(() => new Date());
  const [avail, setAvail] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [pros, setPros] = useState<{ id: string; name: string; services?: string[] }[]>([]);
  const [slots, setSlots] = useState<string[]>([]);
  const [useGcal, setUseGcal] = useState<boolean>(false);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const daysAbort = useRef<AbortController | null>(null);
  const slotsAbort = useRef<AbortController | null>(null);
  const daysTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const slotsTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [focusedDate, setFocusedDate] = useState<Date>(() => new Date());

  // Leer servicio de la URL (fallback por si el estado aún no está)
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sid = params.get('service') || undefined;
    if (!serviceId && sid) {
      setService(sid);
    } else if (sid && serviceId && sid !== serviceId) {
      setService(sid);
    }
  }, [location.search, serviceId, setService]);
  // Rehidratar fecha seleccionada desde el slot si venimos de Confirm
  useEffect(() => {
    if (slotStart && !selected) {
      const d = new Date(slotStart);
      d.setHours(0, 0, 0, 0);
      setSelected(d);
      setDate(toYmd(d));
      setMonth(new Date(d.getFullYear(), d.getMonth(), 1));
      setFocusedDate(d);
    }
  }, [slotStart, selected, setDate]);
  useEffect(() => {
    const sid = new URLSearchParams(location.search).get('service');
    // Si no hay servicio en el store ni en la URL, volver al selector de servicio.
    if (!serviceId && !sid) {
      navigate('/book/service');
    }
  }, [serviceId, navigate, location.search]);

  useEffect(() => {
    if (!serviceId) return;
    let mounted = true;
    const fetchPros = async () => {
      try {
        const json = await api.getProfessionals();
        const filtered = json.filter((p) => !p.services || p.services.includes(serviceId));
        if (mounted) setPros(filtered);
      } catch {
        if (mounted) setPros([]);
      }
    };
    const fetchAvail = async (m: Date) => {
      if (daysTimer.current) clearTimeout(daysTimer.current);
      if (daysAbort.current) daysAbort.current.abort();
      setLoading(true);
      const ctrl = new AbortController();
      daysAbort.current = ctrl;
      daysTimer.current = setTimeout(async () => {
        try {
          const start = startOfMonth(m);
          const end = endOfMonth(m);
          const out = await api.getDaysAvailability({
            service_id: serviceId,
            start: toYmd(start),
            end: toYmd(end),
            professional_id: professionalId ?? undefined,
            use_gcal: useGcal,
          }, { signal: ctrl.signal });
          if (mounted) setAvail(new Set(out.available_days));
        } catch (e: unknown) {
          if (mounted) setAvail(new Set());
        } finally {
          if (mounted) setLoading(false);
        }
      }, 200);
    };
    fetchPros();
    fetchAvail(month);
    return () => {
      mounted = false;
    };
  }, [serviceId, professionalId, month, useGcal]);

  const today = useMemo(() => {
    const t = new Date();
    t.setHours(0, 0, 0, 0);
    return t;
  }, []);

  // límite: hoy + 6 meses
  const maxDate = useMemo(() => {
    const d = new Date(today);
    d.setMonth(d.getMonth() + 6);
    return d;
  }, [today]);

  const selectedValid = useMemo(() => {
    if (!selected) return false;
    const nd = new Date(selected);
    nd.setHours(0, 0, 0, 0);
    if (nd < today || nd > maxDate) return false;
    return avail.has(toYmd(nd));
  }, [selected, today, maxDate, avail]);
  const canContinue = !!slotStart; // requiere elegir un hueco

  const onNext = () => {
    if (!selectedValid || slots.length === 0) return;
    navigate('/book/confirm');
  };

  // Al seleccionar fecha válida, pedir huecos
  useEffect(() => {
    if (!serviceId) return;
    if (!selectedValid) {
      setSlots([]);
      return;
    }
    setDate(toYmd(selected as Date));
    setSlotsLoading(true);
    if (slotsTimer.current) clearTimeout(slotsTimer.current);
    if (slotsAbort.current) slotsAbort.current.abort();
    const ctrl = new AbortController();
    slotsAbort.current = ctrl;
    let mounted = true;
    slotsTimer.current = setTimeout(() => {
      (async () => {
        try {
          const out = await api.getSlots({
            service_id: serviceId,
            date: toYmd(selected as Date),
            professional_id: professionalId ?? undefined,
            use_gcal: useGcal,
          }, { signal: ctrl.signal });
          if (mounted) setSlots(out.slots);
        } catch {
          if (mounted) setSlots([]);
        } finally {
          if (mounted) setSlotsLoading(false);
        }
      })();
    }, 200);
    return () => {
      mounted = false;
      ctrl.abort();
    };
  }, [serviceId, professionalId, selectedValid, useGcal]);

  const steps = [
    { key: 'service', label: 'Servicio', done: true },
    { key: 'date', label: 'Fecha y hora', active: true },
    { key: 'confirm', label: 'Confirmar' },
  ];

  // Fallback mínimo por si algo falla antes de montar el calendario
  if (!serviceId && !new URLSearchParams(location.search).get('service')) {
    return (
      <>
        <BookingSteps />
        <BookingSection title="Selecciona un servicio" subtitle="Elige un servicio para continuar">
          <div className="flex flex-col items-center gap-3">
            <div className="text-base">Necesitas seleccionar un servicio</div>
            <Button onClick={() => navigate('/book/service')} className="h-10 px-5 bg-accent text-[var(--accent-contrast)] hover:bg-emerald-400 transition-colors duration-150">Ir a servicios</Button>
          </div>
        </BookingSection>
      </>
    );
  }

  // Construir grilla del mes actual (lunes-domingo)
  const monthStart = useMemo(() => startOfMonth(month), [month]);
  const monthEnd = useMemo(() => endOfMonth(month), [month]);
  const gridStart = useMemo(() => startOfWeek(monthStart, { weekStartsOn: 1 }), [monthStart]);
  const gridEnd = useMemo(() => endOfWeek(monthEnd, { weekStartsOn: 1 }), [monthEnd]);
  const days = useMemo(() => {
    const list: Date[] = [];
    let d = gridStart;
    while (d <= gridEnd) {
      list.push(d);
      d = addDays(d, 1);
    }
    return list;
  }, [gridStart, gridEnd]);

  // Mover foco con teclado dentro del grid
  const onGridKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    const key = e.key;
    let next = focusedDate || today;
    if (key === 'ArrowLeft') { next = addDays(next, -1); e.preventDefault(); }
    else if (key === 'ArrowRight') { next = addDays(next, 1); e.preventDefault(); }
    else if (key === 'ArrowUp') { next = addDays(next, -7); e.preventDefault(); }
    else if (key === 'ArrowDown') { next = addDays(next, 7); e.preventDefault(); }
    else if (key === 'PageUp') { next = addMonths(next, -1); e.preventDefault(); }
    else if (key === 'PageDown') { next = addMonths(next, 1); e.preventDefault(); }
    else if (key === 'Enter' || key === ' ') {
      // Seleccionar si es habilitado
      const ymd = toYmd(focusedDate);
      const enabled = isSameMonth(focusedDate, month) && !isBefore(focusedDate, today) && !isAfter(focusedDate, maxDate) && avail.has(ymd);
      if (enabled) {
        setSelected(focusedDate);
        setDate(toYmd(focusedDate));
      }
      return;
    } else {
      return;
    }
    // cambiar mes si cruza borde
    if (next.getMonth() !== month.getMonth() || next.getFullYear() !== month.getFullYear()) {
      setMonth(new Date(next.getFullYear(), next.getMonth(), 1));
    }
    setFocusedDate(next);
  }, [focusedDate, month, today, maxDate, avail, setDate]);

  const onPrevMonth = () => setMonth(subMonths(month, 1));
  const onNextMonth = () => setMonth(addMonths(month, 1));

  // Asegurar foco en cambio de mes
  useEffect(() => {
    // Si el focus está fuera del grid actual, llévalo al primer día del mes
    if (focusedDate < gridStart || focusedDate > gridEnd) {
      setFocusedDate(monthStart);
    }
  }, [gridStart, gridEnd, monthStart, focusedDate]);

  return (
    <BookingLayout
      steps={steps}
      title="Selecciona fecha y hora"
      subtitle="Elige cuándo quieres tu cita"
      summary={serviceId ? `Servicio: ${serviceId}` : undefined}
    >
      <div className="flex items-center gap-3">
        <Label htmlFor="professional-select">Profesional:</Label>
        <Select value={professionalId ?? ANY_PRO} onValueChange={(v) => setProfessional(v === ANY_PRO ? null : v)}>
          <SelectTrigger id="professional-select" className="w-64" aria-label="Seleccionar profesional">
            <SelectValue placeholder="Cualquiera" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ANY_PRO}>Cualquiera</SelectItem>
            {pros.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="relative">
        <div className="flex flex-col items-center gap-3">
          <div className="rounded-md border border-neutral-800 bg-neutral-900 p-3 w-full max-w-[360px]">
            <Calendar
              aria-label="Calendario de fechas disponibles"
              mode="single"
              month={month}
              onMonthChange={setMonth}
              selected={selected}
              onSelect={setSelected}
              disabled={isDisabled}
              locale={es}
              captionLayout="dropdown-buttons"
              fromDate={today}
              toDate={maxDate}
              className="rounded-md"
              modifiers={{ available: (day) => avail.has(toYmd(day as Date)) }}
              modifiersClassNames={{ available: 'text-green-300 font-medium' }}
            />
          </div>
          <div className="text-xs text-neutral-400">
            Días en verde = hay disponibilidad para el servicio elegido.
          </div>
        </div>
        <div className="relative">
          <Card className="rounded-2xl border border-[var(--border)] bg-[var(--card)] backdrop-blur shadow-lg shadow-black/20 w-full">
            <CardContent className="p-4">
            {/* Header de calendario */}
            <div className="mb-2">
              <CalendarNav month={month} onPrev={onPrevMonth} onNext={onNextMonth} />
            </div>

            {/* Nombres de días */}
            <div className="grid grid-cols-7 gap-1 sm:gap-1.5 mb-1 text-[11px] uppercase tracking-wide text-muted-foreground">
              {['lu','ma','mi','ju','vi','sá','do'].map((w) => (
                <div key={w} className="h-8 flex items-center justify-center">{w}</div>
              ))}
            </div>

            {/* Grid de días */}
            <div
              key={`${month.getFullYear()}-${month.getMonth()}`}
              role="grid"
              aria-label={format(month, 'LLLL yyyy', { locale: es })}
              className="grid grid-cols-7 gap-1 sm:gap-1.5 cal-fade"
              tabIndex={0}
              onKeyDown={onGridKeyDown}
            >
              {days.map((d) => {
                const ymd = toYmd(d);
                const inMonth = isSameMonth(d, month);
                const outOfRange = isBefore(d, today) || isAfter(d, maxDate);
                const enabled = inMonth && !outOfRange && avail.has(ymd);
                const selectedDay = selected ? isSameDay(d, selected) : false;
                const isFocused = isSameDay(d, focusedDate);
                const classes = [
                  'aspect-square flex items-center justify-center rounded-md text-[13px] sm:text-sm',
                  '[font-variant-numeric:tabular-nums] transition-colors duration-150',
                  isToday(d) ? 'ring-1 ring-white/10' : '',
                  !inMonth ? 'text-muted-foreground/60 cursor-not-allowed' : (
                    enabled ? (selectedDay ? 'bg-accent text-[var(--accent-contrast)]' : 'bg-[var(--accent-weak)] text-emerald-400 hover:bg-[var(--accent-hover)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]') : 'text-muted-foreground/60 cursor-not-allowed'
                  )
                ].filter(Boolean).join(' ');
                return (
                  <button
                    key={ymd}
                    type="button"
                    role="gridcell"
                    aria-selected={selectedDay}
                    aria-disabled={!enabled}
                    aria-current={isToday(d) ? 'date' : undefined}
                    data-today={isToday(d)}
                    data-selected={selectedDay}
                    data-enabled={enabled}
                    data-disabled={!enabled}
                    disabled={!enabled}
                    tabIndex={isFocused ? 0 : -1}
                    onClick={() => {
                      if (!enabled) return;
                      setSelected(d);
                      setDate(ymd);
                      setFocusedDate(d);
                    }}
                    className={classes}
                  >
                    {String(d.getDate())}
                  </button>
                );
              })}
            </div>

            {/* Leyenda */}
            <p className="mt-3 text-xs text-muted-foreground text-center">
              Días en verde = hay disponibilidad para el servicio elegido.
            </p>
            </CardContent>
          </Card>

          {/* Capa de carga */}
          {loading && (
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center rounded-md">
              <div className="text-sm text-neutral-200 bg-neutral-800 px-3 py-2 rounded">Comprobando disponibilidad…</div>
            </div>
          )}
        </div>
        {/* Horarios disponibles */}
        <Card className="mt-6 rounded-2xl border border-[var(--border)] bg-[var(--card)] backdrop-blur shadow-lg shadow-black/20">
          <CardContent className="p-4">
          <div className="mb-3 text-center">
            <h3 className="text-base font-medium">
              {selectedValid ? `Horarios disponibles para ${toYmd(selected as Date)}` : 'Selecciona una fecha'}
            </h3>
            {selectedValid && (
              <p className="text-xs text-muted-foreground mt-1">Haz clic en un horario para continuar</p>
            )}
          </div>

          {slotsLoading && (
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
              {Array.from({ length: 12 }).map((_, i) => (
                <Skeleton key={i} className="h-9 rounded-md" />
              ))}
            </div>
          )}

          {!slotsLoading && selectedValid && (
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
              {slots.map((iso) => {
                return (
                  <Button
                    key={iso}
                    variant="secondary"
                    className="h-9 rounded-md border border-[var(--border)] bg-white/0 hover:bg-white/5 transition-colors duration-150"
                    onClick={() => {
                      setSlot(iso);
                      if (selectedValid) setDate(toYmd(selected as Date));
                    }}
                  >
                    {iso.slice(11, 16)}
                  </Button>
                );
              })}
              {slots.length === 0 && (
                <div className="col-span-full text-center py-6">
                  <div className="text-neutral-400 mb-1">No hay horarios disponibles</div>
                  <div className="text-xs text-muted-foreground">Intenta con otra fecha o profesional</div>
                </div>
              )}
            </div>
          )}

          {/* CTA centrada */}
          <div className="mt-4 flex justify-center">
            <Button disabled={!canContinue || slots.length === 0} onClick={onNext} className="h-11 px-6 bg-accent text-[var(--accent-contrast)] hover:bg-emerald-400 disabled:opacity-50 disabled:pointer-events-none transition-colors duration-150">
              Continuar
            </Button>
          </div>
          </CardContent>
        </Card>
      </BookingSection>
    </>
  );
};

export default BookDate;
