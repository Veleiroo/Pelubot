import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBooking } from '@/store/booking';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { toast } from '@/components/ui/sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { BookingSteps } from '@/components/BookingSteps';

type Professional = { id: string; name: string; services?: string[] };

const BookTime = () => {
  const navigate = useNavigate();
  const { serviceId, date, professionalId, setProfessional, setSlot } = useBooking((s) => ({
    serviceId: s.serviceId,
    date: s.date,
    professionalId: s.professionalId,
    setProfessional: s.setProfessional,
    setSlot: s.setSlot,
  }));
  const [pros, setPros] = useState<Professional[]>([]);
  const [slots, setSlots] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useGcal, setUseGcal] = useState<boolean>(true);

  useEffect(() => {
    if (!serviceId || !date) return;
    let mounted = true;
    (async () => {
      try {
        const json = await api.getProfessionals();
        const filtered = serviceId ? json.filter((p) => !p.services || p.services.includes(serviceId)) : json;
        if (mounted) setPros(filtered);
      } catch (e: any) {
        const msg = e?.message || 'Error cargando profesionales';
        setError(msg);
        toast.error(msg);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [serviceId, date]);

  useEffect(() => {
    if (!serviceId || !date) return;
    let mounted = true;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const out = await api.getSlots({ service_id: serviceId, date, professional_id: professionalId ?? undefined, use_gcal: useGcal });
        if (mounted) setSlots(out.slots);
      } catch (e: any) {
        const msg = e?.message || 'Error cargando horarios';
        setError(msg);
        toast.error(msg);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [serviceId, date, professionalId, useGcal]);

  if (!serviceId || !date) {
    navigate('/book/service');
    return null;
  }

  const onConfirm = (start: string) => {
    setSlot(start);
    navigate('/book/confirm');
  };

  return (
    <div className="mx-auto max-w-2xl p-6 text-white space-y-4 border border-neutral-800 bg-neutral-900 rounded-md">
      <BookingSteps steps={[{ key: 'service', label: 'Servicio', done: true }, { key: 'date', label: 'Fecha y hora', active: true }, { key: 'confirm', label: 'Confirmar' }]} />
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

      <div className="flex items-center gap-2">
        <Switch id="use-gcal" checked={useGcal} onCheckedChange={setUseGcal} />
        <Label htmlFor="use-gcal" className="text-sm text-neutral-300">Comprobar Google Calendar (evitar solapes externos)</Label>
      </div>

      {loading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-10" />
          ))}
        </div>
      )}
      {loading && <div className="text-sm text-neutral-400">Comprobando disponibilidad…</div>}
      {error && <div className="text-red-500">{error}</div>}

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {slots.map((iso) => {
          const time = iso.slice(11, 16); // HH:MM
          return (
            <Button key={iso} variant="secondary" onClick={() => onConfirm(iso)}>
              {time}
            </Button>
          );
        })}
        {!loading && slots.length === 0 && <div>No hay horarios disponibles.</div>}
      </div>
    </div>
  );
};

export default BookTime;
