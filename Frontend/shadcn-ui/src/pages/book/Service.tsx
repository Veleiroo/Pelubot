import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, Service as Svc } from '@/lib/api';
import { useBooking } from '@/store/booking';
import { toast } from '@/components/ui/sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { BookingSection } from '@/components/book/BookingSection';
import { ServiceCard } from '@/components/book/ServiceCard';
import { Scissors, Palette, Sparkles, LucideIcon, Crown, Zap } from 'lucide-react';
import { BookingSteps } from '@/components/BookingSteps';

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

  if (loading)
    return (
      <>
        <BookingSteps />
        <BookingSection title="Selecciona un servicio" subtitle="Elige el servicio que deseas reservar">
          <div role="list" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Skeleton className="h-12 w-12 rounded-xl" />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                </div>
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
            ))}
          </div>
        </BookingSection>
      </>
    );

  if (error)
    return (
      <>
        <BookingSteps />
        <BookingSection title="Selecciona un servicio" subtitle="Elige el servicio que deseas reservar">
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 mb-4">
              <Zap className="h-6 w-6 text-red-400" />
            </div>
            <div className="text-red-400 text-sm font-medium">{error}</div>
          </div>
        </BookingSection>
      </>
    );

  const onSelect = (id: string) => {
    setService(id);
    // Pasamos el servicio en la URL para evitar cualquier condición de carrera del store
    navigate(`/book/date?service=${encodeURIComponent(id)}`);
  };

  const iconMap: Record<string, LucideIcon> = {
    corte: Scissors,
    tinte: Palette,
    barba: Sparkles,
    premium: Crown,
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
