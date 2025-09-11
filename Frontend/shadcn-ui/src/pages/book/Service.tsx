import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, Service as Svc } from '@/lib/api';
import { useBooking } from '@/store/booking';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import BookingLayout from '@/components/BookingLayout';

const Service = () => {
  const navigate = useNavigate();
  const setService = useBooking((s) => s.setService);
  const [services, setServices] = useState<Svc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const items = await api.getServices();
        if (mounted) setServices(items);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Error cargando servicios';
        setError(msg);
        toast.error(msg);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const steps = [
    { key: 'service', label: 'Servicio', active: true },
    { key: 'date', label: 'Fecha y hora' },
    { key: 'confirm', label: 'Confirmar' },
  ];

  if (loading)
    return (
      <BookingLayout steps={steps} title="Selecciona un servicio" subtitle="Elige el servicio que deseas reservar">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="border-neutral-800 bg-neutral-900">
              <CardHeader>
                <Skeleton className="h-6 w-40" />
              </CardHeader>
              <CardContent className="flex items-center justify-between">
                <div className="space-y-2 w-full">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-24" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </BookingLayout>
    );

  if (error)
    return (
      <BookingLayout steps={steps} title="Selecciona un servicio" subtitle="Elige el servicio que deseas reservar">
        <div className="text-red-500">{error}</div>
      </BookingLayout>
    );

  const onSelect = (id: string) => {
    setService(id);
    // Pasamos el servicio en la URL para evitar cualquier condición de carrera del store
    navigate(`/book/date?service=${encodeURIComponent(id)}`);
  };

  return (
    <BookingLayout steps={steps} title="Selecciona un servicio" subtitle="Elige el servicio que deseas reservar">
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {services.map((s) => (
          <Card key={s.id} className="border-neutral-800 bg-neutral-900 text-white hover:bg-neutral-800 transition-colors">
            <CardHeader className="pb-3">
              <CardTitle className="text-xl">{s.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-neutral-300">
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                  <span>Duración: {s.duration_min} minutos</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-neutral-300">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span>Precio: {s.price_eur} €</span>
                </div>
              </div>
              <Button onClick={() => onSelect(s.id)} className="w-full" size="lg">
                Seleccionar
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </BookingLayout>
  );
};

export default Service;
