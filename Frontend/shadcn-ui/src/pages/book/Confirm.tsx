import { useNavigate } from 'react-router-dom';
import { useBooking } from '@/store/booking';
import { Button } from '@/components/ui/button';
import { useState } from 'react';
import { api } from '@/lib/api';
import { toast } from '@/components/ui/sonner';
import { BookingSteps } from '@/components/BookingSteps';

const BookConfirm = () => {
  const navigate = useNavigate();
  const { serviceId, professionalId, slotStart, reset } = useBooking();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  if (!serviceId || !slotStart) {
    // Si hay servicio en la URL pero falta slot, vuelve al calendario
    const params = new URLSearchParams(window.location.search);
    const sid = params.get('service');
    navigate(sid ? `/book/date?service=${encodeURIComponent(sid)}` : '/book/service');
    return null;
  }

  const onConfirm = async () => {
    setLoading(true);
    setError(null);
    setOk(null);
    try {
      let message: string | null = null;
      if (professionalId) {
        const res = await api.createReservation({ service_id: serviceId, professional_id: professionalId, start: slotStart });
        message = res.message;
      } else {
        // Sin profesional seleccionado: intentar con la lista de profesionales que soportan el servicio
        const resp = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8776'}/professionals`);
        const pros: { id: string; services?: string[] }[] = await resp.json();
        const candidates = pros.filter((p) => !p.services || p.services.includes(serviceId));
        let success = false;
        for (const p of candidates) {
          try {
            const res = await api.createReservation({ service_id: serviceId, professional_id: p.id, start: slotStart });
            message = res.message;
            success = true;
            break;
          } catch {
            // probar siguiente
          }
        }
        if (!success) throw new Error('No fue posible crear la reserva en ninguno de los profesionales');
      }
      setOk(message);
      toast.success('Reserva creada');
      reset();
    } catch (e: any) {
      const msg = e?.message || 'Error creando la reserva';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl p-6 text-white space-y-4 border border-neutral-800 bg-neutral-900 rounded-md">
      <BookingSteps steps={[{ key: 'service', label: 'Servicio', done: true }, { key: 'date', label: 'Fecha y hora', done: true }, { key: 'confirm', label: 'Confirmar', active: true }]} />
      <h2 className="text-xl">Confirmar reserva</h2>
      <div className="text-sm text-neutral-300">
        <div>Servicio: {serviceId}</div>
        <div>Profesional: {professionalId || 'cualquiera'}</div>
        <div>Inicio: {slotStart.replace('T', ' ').slice(0, 16)}</div>
      </div>
      {error && <div className="text-red-500">{error}</div>}
      {ok && <div className="text-green-500 break-all">{ok}</div>}
      <div className="flex gap-2">
        <Button variant="secondary" onClick={() => navigate('/book/time')}>Volver</Button>
        <Button onClick={onConfirm} disabled={loading}>{loading ? 'Creando…' : 'Confirmar'}</Button>
      </div>
    </div>
  );
};

export default BookConfirm;
