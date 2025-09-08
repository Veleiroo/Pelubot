import { useLocation, useNavigate } from 'react-router-dom';
import { useBooking } from '@/store/booking';
import { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { es } from 'date-fns/locale';

const toYmd = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
};

const startOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth(), 1);
const endOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth() + 1, 0);

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
  const [slotsLoading, setSlotsLoading] = useState(false);

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
  useEffect(() => {
    if (!serviceId) navigate('/book/service');
  }, [serviceId, navigate]);

  useEffect(() => {
    if (!serviceId) return;
    let mounted = true;
    const fetchPros = async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8776'}/professionals`);
        const json: { id: string; name: string; services?: string[] }[] = await res.json();
        const filtered = json.filter((p) => !p.services || p.services.includes(serviceId));
        if (mounted) setPros(filtered);
      } catch {
        if (mounted) setPros([]);
      }
    };
    const fetchAvail = async (m: Date) => {
      setLoading(true);
      try {
        const start = startOfMonth(m);
        const end = endOfMonth(m);
        const out = await api.getDaysAvailability({
          service_id: serviceId,
          start: toYmd(start),
          end: toYmd(end),
          professional_id: professionalId ?? undefined,
        });
        if (mounted) setAvail(new Set(out.available_days));
      } catch (e) {
        if (mounted) setAvail(new Set());
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchPros();
    fetchAvail(month);
    return () => {
      mounted = false;
    };
  }, [serviceId, professionalId, month]);

  const today = useMemo(() => {
    const t = new Date();
    t.setHours(0, 0, 0, 0);
    return t;
  }, []);

  const isDisabled = (d: Date) => {
    const nd = new Date(d);
    nd.setHours(0, 0, 0, 0);
    if (nd < today) return true;
    return !avail.has(toYmd(nd));
  };

  const selectedValid = selected && !isDisabled(selected as Date);
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
    let mounted = true;
    (async () => {
      try {
        const out = await api.getSlots({
          service_id: serviceId,
          date: toYmd(selected as Date),
          professional_id: professionalId ?? undefined,
        });
        if (mounted) setSlots(out.slots);
      } catch {
        if (mounted) setSlots([]);
      } finally {
        if (mounted) setSlotsLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [serviceId, professionalId, selectedValid]);

  return (
    <div className="mx-auto max-w-3xl p-6 text-white space-y-4">
      <h2 className="text-xl">Selecciona fecha y hora</h2>

      <div className="flex items-center gap-3">
        <span>Profesional:</span>
        <Select value={professionalId ?? ''} onValueChange={(v) => setProfessional(v || null)}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Cualquiera" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Cualquiera</SelectItem>
            {pros.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="relative">
        <Calendar
          mode="single"
          month={month}
          onMonthChange={setMonth}
          selected={selected}
          onSelect={setSelected}
          disabled={isDisabled}
          locale={es}
          className="rounded-md border border-neutral-800 bg-neutral-900"
          modifiers={{ available: (day) => avail.has(toYmd(day as Date)) }}
          modifiersClassNames={{ available: 'text-green-300' }}
        />
        {loading && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center rounded-md">
            <div className="text-sm text-neutral-200 bg-neutral-800 px-3 py-2 rounded">Comprobando disponibilidad…</div>
          </div>
        )}
      </div>
      {/* Huecos disponibles */}
      <div className="space-y-2">
        <div className="text-sm text-neutral-400">{selectedValid ? `Huecos para ${toYmd(selected as Date)}` : 'Elige un día con disponibilidad'}</div>
        {slotsLoading && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        )}
        {!slotsLoading && selectedValid && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {slots.map((iso) => (
              <Button
                key={iso}
                variant={slotStart === iso ? 'default' : 'secondary'}
                onClick={() => {
                  setSlot(iso);
                  // asegura fecha en store
                  if (selectedValid) {
                    setDate(toYmd(selected as Date));
                  }
                  // navegación inmediata a Confirmar, pasando service en la URL por robustez
                  const q = serviceId ? `?service=${encodeURIComponent(serviceId)}` : '';
                  navigate(`/book/confirm${q}`);
                }}
              >
                {iso.slice(11, 16)}
              </Button>
            ))}
            {slots.length === 0 && <div>No hay horarios disponibles.</div>}
          </div>
        )}
      </div>

      <div className="mt-1 flex justify-end">
        <Button disabled={!canContinue || slots.length === 0} onClick={onNext}>
          Continuar
        </Button>
      </div>
    </div>
  );
};

export default BookDate;
