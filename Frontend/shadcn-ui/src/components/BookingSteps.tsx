import { cn } from '@/lib/utils';

export type BookingStep = { key: string; label: string; active?: boolean; done?: boolean };

export function BookingSteps({ steps }: { steps?: BookingStep[] }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { serviceId, date, slotStart } = useBooking((s) => ({ serviceId: s.serviceId, date: s.date, slotStart: s.slotStart }));

  const routeToStep = (path: string): Step => {
    if (path.startsWith('/book/confirm')) return 'confirm';
    if (path.startsWith('/book/date')) return 'date';
    return 'service';
  };
  const current: Step = routeToStep(location.pathname);
  const order: Step[] = ['service', 'date', 'confirm'];
  const completed = (k: Step) => order.indexOf(k) < order.indexOf(current);
  const canGo = (k: Step): boolean => {
    if (k === 'service') return true;
    if (k === 'date') return !!serviceId;
    if (k === 'confirm') return !!serviceId && !!(slotStart || date);
    return false;
  };
  const go = (k: Step) => {
    const map: Record<Step, string> = { service: '/book/service', date: '/book/date', confirm: '/book/confirm' };
    navigate(map[k]);
  };

  const items: { key: Step; label: string }[] = [
    { key: 'service', label: 'Servicio' },
    { key: 'date', label: 'Fecha y hora' },
    { key: 'confirm', label: 'Confirmar' },
  ];

export function BookingSteps({ steps }: { steps: BookingStep[] }) {
  const activeIdx = steps.findIndex((s) => s.active);
  const progress = ((activeIdx >= 0 ? activeIdx + 1 : 0) / steps.length) * 100;

  return (
    <nav aria-label="Progreso de reserva" className="mx-auto max-w-4xl px-6 sm:px-8 mb-8">
      <ol className="flex items-center justify-between">
        {items.map((s, i) => {
          const isCurrent = s.key === current;
          const isDone = completed(s.key);
          const enabled = canGo(s.key) || isDone || isCurrent;
          return (
            <li key={s.key} className="flex flex-col items-center">
              <button
                aria-current={isCurrent ? 'step' : undefined}
                aria-label={s.label}
                disabled={!enabled}
                onClick={() => enabled && go(s.key)}
                className={[
                  'flex items-center justify-center w-9 h-9 rounded-full text-xs font-semibold transition-colors duration-150',
                  isDone
                    ? 'bg-accent text-[var(--accent-contrast)]'
                    : isCurrent
                    ? 'ring-2 ring-[var(--accent)] text-foreground'
                    : 'text-muted-foreground hover:text-foreground',
                ].join(' ')}
              >
                {isDone ? <Check className="h-4 w-4" /> : <span>{i + 1}</span>}
              </button>
              <span className={[
                'mt-2 text-xs transition-colors duration-150',
                isCurrent ? 'text-foreground font-medium' : isDone ? 'text-foreground' : 'text-muted-foreground',
              ].join(' ')}>
                {s.label}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export default BookingSteps;
