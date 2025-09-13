import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useBooking } from '@/store/booking';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { toast } from '@/components/ui/sonner';
import { BookingSteps } from '@/components/BookingSteps';
import { BookingSection } from '@/components/book/BookingSection';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { fmtEuro, fmtDateLong, fmtTime } from '@/lib/format';
import { CheckCircle2, Calendar, Clock, User, Scissors, ArrowLeft } from 'lucide-react';

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
      }, 3000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error creando la reserva';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (isoString: string) => `${fmtDateLong(isoString)}, ${fmtTime(isoString)}h`;

  if (!serviceId || !slotStart) {
    return (
      <>
          <BookingSteps />
          <BookingSection title="Confirmar reserva" subtitle="Revisa los detalles antes de confirmar">
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-r from-amber-500/20 to-amber-400/20 border border-amber-500/30 mb-6">
                <Calendar className="h-10 w-10 text-amber-400" />
              </div>
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-white">Faltan datos de tu reserva</h3>
                <p className="text-slate-400">Necesitas completar los pasos anteriores</p>
                <Button
                  variant="secondary"
                  onClick={() => navigate('/book/service')}
                  className="bg-gradient-to-r from-emerald-500/20 to-emerald-400/20 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/30"
                >
                  Ir a seleccionar servicio
                </Button>
              </div>
            </div>
          </BookingSection>
      </>
    );
  }

  return (
    <>
        <BookingSteps />
        <BookingSection title="Confirmar reserva" subtitle="Revisa los detalles y confirma tu cita">
      <Card className="rounded-2xl border border-[var(--border)] bg-[var(--card)] backdrop-blur shadow-lg shadow-black/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold">Resumen</CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-emerald-400 font-medium">
              <Scissors className="h-4 w-4" />
              <span>Servicio</span>
            </div>
            <div className="text-lg font-medium text-foreground">{service?.name || serviceId}</div>
            <div className="text-sm text-muted-foreground">{service?.duration_min} min · {fmtEuro(service?.price_eur)}</div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-emerald-400 font-medium">
              <User className="h-4 w-4" />
              <span>Profesional</span>
            </div>
            <div className="text-lg font-medium text-foreground">{professional?.name || 'Cualquiera disponible'}</div>
          </div>
          <div className="space-y-2 md:col-span-2">
            <div className="flex items-center gap-2 text-sm text-emerald-400 font-medium">
              <Calendar className="h-4 w-4" />
              <span>Fecha y hora</span>
            </div>
            <div className="flex items-center gap-2 text-lg font-medium text-foreground">
              <Clock className="h-5 w-5 text-emerald-400" />
              <span>{formatDateTime(slotStart)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-red-400 mt-0.5" />
            <div>
              <div className="text-red-400 font-semibold">Error al crear la reserva</div>
              <div className="text-red-300 text-sm mt-1">{error}</div>
            </div>
          </div>
        </div>
      )}

      {ok && (
        <div className="rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-400 mt-0.5" />
            <div>
              <div className="text-emerald-400 font-semibold">¡Reserva creada!</div>
              <div className="text-emerald-300 text-sm mt-1 break-all">{ok}</div>
            </div>
          </div>
        </div>
      )}

      <div className="mt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
        <Button
          variant="secondary"
          onClick={() => navigate('/book/date')}
          disabled={loading}
          className="h-11 px-6"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <Button
          onClick={onConfirm}
          disabled={loading || !!ok}
          className="h-11 px-6 bg-accent text-[var(--accent-contrast)] hover:bg-emerald-400 disabled:opacity-50 disabled:pointer-events-none transition-colors duration-150"
        >
          {loading ? 'Creando reserva…' : 'Confirmar reserva'}
        </Button>
      </div>
      </BookingSection>
    </>
  );
};

export default BookConfirm;
