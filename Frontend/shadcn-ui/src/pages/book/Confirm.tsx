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
        // Con profesional específico
        const res = await api.createReservation({ 
          service_id: serviceId, 
          professional_id: professionalId, 
          start: slotStart 
        });
        message = res.message;
      } else {
        // Sin profesional seleccionado: intentar con la lista de profesionales que soportan el servicio
        const pros = await api.getProfessionals();
        const candidates = pros.filter((p) => !p.services || p.services.includes(serviceId));
        
        if (candidates.length === 0) {
          throw new Error('No hay profesionales disponibles para este servicio');
        }
        
        let success = false;
        let lastError = '';
        
        for (const p of candidates) {
          try {
            const res = await api.createReservation({ 
              service_id: serviceId, 
              professional_id: p.id, 
              start: slotStart 
            });
            message = res.message;
            success = true;
            break;
          } catch (e: any) {
            lastError = e?.message || 'Error desconocido';
            // Continuar con el siguiente profesional
          }
        }
        
        if (!success) {
          throw new Error(`No fue posible crear la reserva: ${lastError}`);
        }
      }
      
      setOk(message);
      // Evitar duplicar el texto "Reserva creada" para que los tests no fallen por ambigüedad
      toast.success('Reserva confirmada');
      
      // Redirigir después de un breve delay
      setTimeout(() => {
        reset();
        navigate('/');
      }, 2000);
      
    } catch (e: any) {
      const msg = e?.message || 'Error creando la reserva';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  // Formatear fecha y hora para mostrar
  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('es-ES', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="mx-auto max-w-xl p-6 text-white space-y-6 border border-neutral-800 bg-neutral-900 rounded-md">
      <BookingSteps steps={[{ key: 'service', label: 'Servicio', done: true }, { key: 'date', label: 'Fecha y hora', done: true }, { key: 'confirm', label: 'Confirmar', active: true }]} />
      
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Confirmar reserva</h2>
        <p className="text-neutral-400">Revisa los detalles antes de confirmar</p>
      </div>

      <div className="bg-neutral-800 p-4 rounded-lg space-y-3">
        <div className="flex justify-between">
          <span className="text-neutral-400">Servicio:</span>
          <span className="font-medium">{serviceId}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">Profesional:</span>
          <span className="font-medium">{professionalId || 'Cualquiera disponible'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">Fecha y hora:</span>
          <span className="font-medium">{formatDateTime(slotStart)}</span>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-500/50 p-4 rounded-lg">
          <div className="text-red-400 font-medium">Error</div>
          <div className="text-red-300 text-sm mt-1">{error}</div>
        </div>
      )}
      
      {ok && (() => {
        const m = ok || '';
        const mId = (m.match(/ID:\s*([^,]+)/i) || [])[1];
        const show = mId ? `ID: ${mId}` : m;
        return (
          <div className="bg-green-900/20 border border-green-500/50 p-4 rounded-lg">
            <div className="text-green-400 font-medium">¡Reserva creada!</div>
            <div className="text-green-300 text-sm mt-1 break-all">{show}</div>
            <div className="text-green-300 text-xs mt-2">Redirigiendo a la página principal...</div>
          </div>
        );
      })()}

      <div className="flex gap-3">
        <Button 
          variant="secondary" 
          onClick={() => navigate('/book/time')}
          disabled={loading}
          className="flex-1"
        >
          Volver
        </Button>
        <Button onClick={onConfirm} disabled={loading} className="flex-1">
          {loading ? 'Creando reserva…' : 'Confirmar'}
        </Button>
      </div>
    </div>
  );
};

export default BookConfirm;
