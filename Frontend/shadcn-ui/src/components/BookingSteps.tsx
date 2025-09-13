import { cn } from '@/lib/utils';

export type BookingStep = { key: string; label: string; active?: boolean; done?: boolean };

const DEFAULT_STEPS: BookingStep[] = [
  { key: 'service', label: 'Servicio' },
  { key: 'date', label: 'Fecha y hora' },
  { key: 'confirm', label: 'Confirmar' },
];

export function BookingSteps({ steps = DEFAULT_STEPS }: { steps?: BookingStep[] }) {
  const activeIdx = steps.findIndex((s) => s.active);
  const progress = ((activeIdx >= 0 ? activeIdx + 1 : 0) / steps.length) * 100;

  return (
    <div className="mb-4" aria-label="Progreso de reserva">
      <div className="h-1 bg-neutral-800 rounded">
        <div
          className="h-full bg-[#00D4AA] rounded transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="flex items-center gap-3 text-sm mt-2" role="list">
        {steps.map((s, i) => (
          <div key={s.key} className="flex items-center gap-3" role="listitem">
            <div
              className={cn(
                'px-2 py-1 rounded border',
                s.active
                  ? 'border-[#00D4AA] text-[#00D4AA]'
                  : s.done
                  ? 'border-neutral-600 text-neutral-300'
                  : 'border-neutral-800 text-neutral-500'
              )}
              aria-current={s.active ? 'step' : undefined}
            >
              <span className="font-medium mr-1">{i + 1}.</span> {s.label}
            </div>
            {i < steps.length - 1 && <div className="w-6 h-px bg-neutral-700" />}
          </div>
        ))}
      </div>
    </div>
  );
}
