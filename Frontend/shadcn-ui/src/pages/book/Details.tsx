import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import BookingLayout from '@/components/BookingLayout';

const BookDetails = () => {
  const navigate = useNavigate();
  const steps = [
    { key: 'service', label: 'Servicio', done: true },
    { key: 'date', label: 'Fecha y hora', done: true },
    { key: 'details', label: 'Detalles', active: true },
    { key: 'confirm', label: 'Confirmar' },
  ];
  return (
    <BookingLayout steps={steps} title="Detalles" subtitle="No se requieren detalles adicionales">
      <div className="text-neutral-400 text-center">Continúa a la confirmación.</div>
      <div className="flex justify-end">
        <Button onClick={() => navigate('/book/confirm')}>Continuar</Button>
      </div>
    </BookingLayout>
  );
};

export default BookDetails;
