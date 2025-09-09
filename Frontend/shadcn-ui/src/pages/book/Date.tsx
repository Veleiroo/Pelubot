import { useLocation, useNavigate } from 'react-router-dom';
import { useBooking } from '@/store/booking';
import { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
// Calendario avanzado deshabilitado por estabilidad en entornos limitados.
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { es } from 'date-fns/locale';
import { BookingSteps } from '@/components/BookingSteps';

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
  const [useGcal, setUseGcal] = useState<boolean>(true);
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
      setLoading(true);
      try {
        const start = startOfMonth(m);
        const end = endOfMonth(m);
        const out = await api.getDaysAvailability({
          service_id: serviceId,
          start: toYmd(start),
          end: toYmd(end),
          professional_id: professionalId ?? undefined,
          use_gcal: useGcal,
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
  }, [serviceId, professionalId, month, useGcal]);

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
          use_gcal: useGcal,
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
  }, [serviceId, professionalId, selectedValid, useGcal]);

  // Fallback mínimo por si algo falla antes de montar el calendario
  if (!serviceId && !new URLSearchParams(location.search).get('service')) {
    return (
      <div className="min-h-screen flex items-center justify-center text-white">
        <div>
          <div className="text-xl mb-2">Selecciona un servicio para continuar</div>
          <Button onClick={() => navigate('/book/service')}>Ir a servicios</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-6 text-white space-y-6">
      <BookingSteps steps={[{ key: 'service', label: 'Servicio', done: true }, { key: 'date', label: 'Fecha y hora', active: true }, { key: 'confirm', label: 'Confirmar' }]} />
      
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">Selecciona fecha y hora</h1>
        <p className="text-neutral-400">Elige cuándo quieres tu cita</p>
      </div>

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
        <div className="rounded-md border border-neutral-800 bg-neutral-900 p-4 text-sm text-neutral-300">
          Selecciona la fecha con el selector y luego el horario disponible.
        </div>
        <div className="mt-3 flex items-center gap-2">
          <Switch id="use-gcal" checked={useGcal} onCheckedChange={setUseGcal} />
          <Label htmlFor="use-gcal" className="text-sm text-neutral-300">Comprobar Google Calendar (evitar solapes externos)</Label>
        </div>
        {loading && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center rounded-md">
            <div className="text-sm text-neutral-200 bg-neutral-800 px-3 py-2 rounded">Comprobando disponibilidad…</div>
          </div>
        )}
        {/* Selector de fecha simple (siempre disponible) */}
        <div className="mt-3 text-sm text-neutral-300">
          <div>Elige una fecha:</div>
          <input
            type="date"
            className="mt-2 bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-sm"
            onChange={(e) => {
              const v = e.currentTarget.value;
              if (v) setSelected(new Date(v + 'T00:00:00'));
            }}
          />
        </div>
      </div>
      {/* Huecos disponibles */}
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
    </div>
  );
};

export default BookDate;
