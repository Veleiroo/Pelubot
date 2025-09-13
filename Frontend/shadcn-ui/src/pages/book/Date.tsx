import { useLocation, useNavigate } from 'react-router-dom';
import { useBooking } from '@/store/booking';
import { useEffect, useMemo, useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
// Calendario visual opcional. Si `VITE_ENABLE_CALENDAR` está activo se muestra; en caso contrario el usuario usa el selector nativo de fecha. En ambos casos se listan los huecos.
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { es } from 'date-fns/locale';
import BookingLayout from '@/components/BookingLayout';

const toYmd = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
};

const startOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth(), 1);
const endOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth() + 1, 0);

const ANY_PRO = '__any__';

const BookDate = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { serviceId, serviceName, professionalId, slotStart, setProfessional, setDate, setSlot, setService } = useBooking((s) => ({
    serviceId: s.serviceId,
    serviceName: s.serviceName,
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
  const [useGcal] = useState<boolean>(false);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const daysAbort = useRef<AbortController | null>(null);
  const slotsAbort = useRef<AbortController | null>(null);
  const daysTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const slotsTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Lee el servicio de la URL como respaldo por si el estado aún no está sincronizado.
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sid = params.get('service') || undefined;
    if (!serviceId && sid) {
      setService(sid);
    } else if (sid && serviceId && sid !== serviceId) {
      setService(sid);
    }
  }, [location.search, serviceId, setService]);

  // Si solo tenemos el ID del servicio, obtenemos su nombre para mostrarlo en el resumen.
  useEffect(() => {
    if (!serviceId || serviceName) return;
    (async () => {
      try {
        const items = await api.getServices();
        const found = items.find((s) => s.id === serviceId);
        if (found) setService(serviceId, found.name);
      } catch {
        /* noop */
      }
    })();
  }, [serviceId, serviceName, setService]);
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

  // Límite: hoy + 6 meses.
  const maxDate = useMemo(() => {
    const d = new Date(today);
    d.setMonth(d.getMonth() + 6);
    return d;
  }, [today]);

  const isDisabled = (d: Date) => {
    const nd = new Date(d);
    nd.setHours(0, 0, 0, 0);
    if (nd < today) return true;
    return !avail.has(toYmd(nd));
  };

  const selectedValid = selected && !isDisabled(selected as Date);
  const canContinue = !!slotStart; // Requiere elegir un hueco.

  const onNext = () => {
    if (!selectedValid || slots.length === 0) return;
    navigate('/book/confirm');
  };

  // Al seleccionar una fecha válida se solicitan los huecos.
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

  // Fallback mínimo por si algo falla antes de montar el calendario.
  if (!serviceId && !new URLSearchParams(location.search).get('service')) {
    return (
      <BookingLayout steps={steps} title="Selecciona un servicio" subtitle="Elige un servicio para continuar">
        <div className="flex flex-col items-center gap-4">
          <div className="text-xl">Necesitas seleccionar un servicio</div>
          <Button onClick={() => navigate('/book/service')}>Ir a servicios</Button>
        </div>
      </BookingLayout>
    );
  }

  return (
    <BookingLayout
      steps={steps}
      title="Selecciona fecha y hora"
      subtitle="Elige cuándo quieres tu cita"
      summary={serviceId ? `Servicio: ${serviceName ?? serviceId}` : undefined}
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
        {/* Toggle avanzado de GCal oculto en interfaz pública. Si quieres mostrarlo, quita este bloque. */}
        {loading && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center rounded-md">
            <div className="text-sm text-neutral-200 bg-neutral-800 px-3 py-2 rounded">Comprobando disponibilidad…</div>
          </div>
        )}
        
      </div>
      {/* Huecos disponibles. */}
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-2">
            {selectedValid ? `Horarios disponibles para ${toYmd(selected as Date)}` : 'Selecciona una fecha'}
          </h3>
          {selectedValid && (
            <p className="text-sm text-neutral-400">
              Haz clic en un horario para continuar
            </p>
          )}
        </div>
        
        {slotsLoading && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="h-12 rounded-lg" />
            ))}
          </div>
        )}
        
        {!slotsLoading && selectedValid && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {slots.map((iso) => (
              <Button
                key={iso}
                variant={slotStart === iso ? 'default' : 'outline'}
                size="lg"
                className={`h-12 ${
                  slotStart === iso 
                    ? 'bg-blue-600 hover:bg-blue-700' 
                    : 'border-neutral-600 hover:bg-neutral-800'
                }`}
                onClick={() => {
                  setSlot(iso);
                  // Asegura la fecha en el store.
                  if (selectedValid) {
                    setDate(toYmd(selected as Date));
                  }
                  // Navega a Confirmar pasando parámetros robustos.
                  const params = new URLSearchParams();
                  if (serviceId) params.set('service', serviceId);
                  params.set('start', iso);
                  if (professionalId) params.set('pro', professionalId);
                  navigate(`/book/confirm?${params.toString()}`);
                }}
              >
                {iso.slice(11, 16)}
              </Button>
            ))}
            {slots.length === 0 && (
              <div className="col-span-full text-center py-8">
                <div className="text-neutral-400 mb-2">No hay horarios disponibles</div>
                <div className="text-sm text-neutral-500">Intenta con otra fecha o profesional</div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mt-1 flex justify-end">
        <Button disabled={!canContinue || slots.length === 0} onClick={onNext}>
          Continuar
        </Button>
      </div>
    </BookingLayout>
  );
};

export default BookDate;
