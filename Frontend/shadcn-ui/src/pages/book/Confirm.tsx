import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useBooking } from '@/store/booking';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { toast } from '@/components/ui/sonner';
import BookingLayout from '@/components/BookingLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { fmtEuro, fmtDateLong, fmtTime } from '@/lib/format';
import { CheckCircle2 } from 'lucide-react';

const BookConfirm = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { serviceId, professionalId, slotStart, reset, setService, setProfessional, setSlot } = useBooking();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [services, setServices] = useState<{ id: string; name: string; duration_min: number; price_eur: number }[]>([]);
  const [pros, setPros] = useState<{ id: string; name: string }[]>([]);

  useEffect(() => {
    (async () => {
      try { setServices(await api.getServices()); } catch {}
      try { setPros(await api.getProfessionals()); } catch {}
    })();
  }, []);

  const service = useMemo(() => services.find(s => s.id === serviceId), [services, serviceId]);
  const professional = useMemo(() => pros.find(p => p.id === professionalId), [pros, professionalId]);

  useEffect(() => {
    if (serviceId && slotStart) return;
    const p = new URLSearchParams(location.search);
    const sid = p.get('service') || undefined;
    const start = p.get('start') || undefined;
    const pro = p.get('pro');
    if (sid) setService(sid);
    if (start) setSlot(start);
    if (pro !== null) setProfessional(pro || null);
  }, [serviceId, slotStart, location.search, setService, setSlot, setProfessional]);

  const onConfirm = async () => {
    setLoading(true);
    setError(null);
    setOk(null);
    try {
      let message: string | null = null;

      if (professionalId) {
        const res = await api.createReservation({
          service_id: serviceId,
          professional_id: professionalId,
          start: slotStart,
        });
        message = res.message;
      } else {
        const pros = await api.getProfessionals();
        const candidates = pros.filter((p) => !p.services || p.services.includes(serviceId));
        if (candidates.length === 0) throw new Error('No hay profesionales disponibles para este servicio');
        let success = false;
        let lastError = '';
        for (const p of candidates) {
          try {
            const res = await api.createReservation({
              service_id: serviceId,
              professional_id: p.id,
              start: slotStart,
            });
            message = res.message;
            success = true;
            break;
          } catch (e: unknown) {
            lastError = e instanceof Error ? e.message : 'Error desconocido';
          }
        }
        if (!success) throw new Error(`No fue posible crear la reserva: ${lastError}`);
      }

      setOk(message);
      toast.success('Reserva confirmada');
      setTimeout(() => {
        reset();
        navigate('/');
      }, 2000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error creando la reserva';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (isoString: string) => `${fmtDateLong(isoString)}, ${fmtTime(isoString)}h`;

  const steps = [
    { key: 'service', label: 'Servicio', done: !!serviceId },
    { key: 'date', label: 'Fecha y hora', done: !!slotStart },
    { key: 'confirm', label: 'Confirmar', active: true },
  ];

  if (!serviceId || !slotStart) {
    return (
      <BookingLayout steps={steps} title="Confirmar reserva" subtitle="Revisa los detalles antes de confirmar">
        <div className="text-neutral-300">Cargando datos de tu reserva…</div>
        <Button variant="secondary" onClick={() => navigate('/book/service')}>Ir a seleccionar servicio</Button>
      </BookingLayout>
    );
  }

  return (
    <BookingLayout steps={steps} title="Confirmar reserva" subtitle="Revisa los detalles antes de confirmar">
      <Card className="border-neutral-800 bg-neutral-900">
        <CardHeader className="pb-2">
          <CardTitle className="text-white">Resumen</CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="text-sm text-neutral-400">Servicio</div>
            <div className="text-lg font-medium">{service?.name || serviceId}</div>
            <div className="text-sm text-neutral-300">{service?.duration_min} min · {fmtEuro(service?.price_eur)}</div>
          </div>
          <div className="space-y-2">
            <div className="text-sm text-neutral-400">Profesional</div>
            <div className="text-lg font-medium">{professional?.name || 'Cualquiera disponible'}</div>
          </div>
          <div className="space-y-2 md:col-span-2">
            <div className="text-sm text-neutral-400">Fecha y hora</div>
            <div className="text-lg font-medium">{formatDateTime(slotStart)}</div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="bg-red-900/20 border border-red-500/50 p-4 rounded-lg">
          <div className="text-red-400 font-medium">Error</div>
          <div className="text-red-300 text-sm mt-1">{error}</div>
        </div>
      )}

      {ok && (
        <div className="bg-green-900/20 border border-green-500/50 p-4 rounded-lg flex items-start gap-3">
          <CheckCircle2 className="text-green-400 mt-0.5" />
          <div>
            <div className="text-green-400 font-medium">¡Reserva creada!</div>
            <div className="text-green-300 text-sm mt-1 break-all">{ok}</div>
            <div className="text-green-300 text-xs mt-2">Redirigiendo a la página principal...</div>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <Button variant="secondary" onClick={() => navigate('/book/time')} disabled={loading} className="flex-1">
          Volver
        </Button>
        <Button onClick={onConfirm} disabled={loading} className="flex-1">
          {loading ? 'Creando reserva…' : 'Confirmar'}
        </Button>
      </div>
    </BookingLayout>
  );
};

export default BookConfirm;
