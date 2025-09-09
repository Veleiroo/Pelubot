import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, Service as Svc } from '@/lib/api';
import { useBooking } from '@/store/booking';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BookingSteps } from '@/components/BookingSteps';
import { Skeleton } from '@/components/ui/skeleton';

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
      } catch (e: any) {
        const msg = e?.message || 'Error cargando servicios';
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

  if (loading)
    return (
      <div className="mx-auto max-w-3xl p-6 grid gap-4 sm:grid-cols-2">
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
    );
  if (error) return <div className="p-6 text-red-500">{error}</div>;

  const onSelect = (id: string) => {
    setService(id);
    // Pasamos el servicio en la URL para evitar cualquier condición de carrera del store
    navigate(`/book/date?service=${encodeURIComponent(id)}`);
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <BookingSteps steps={[{ key: 'service', label: 'Servicio', active: true }, { key: 'date', label: 'Fecha y hora' }, { key: 'confirm', label: 'Confirmar' }]} />
      
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Selecciona un servicio</h1>
        <p className="text-neutral-400">Elige el servicio que deseas reservar</p>
      </div>

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
              <Button 
                onClick={() => onSelect(s.id)} 
                className="w-full"
                size="lg"
              >
                Seleccionar
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Service;
