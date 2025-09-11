import { cn } from '@/lib/utils';

export type BookingStep = {
  key: string;
  label: string;
  active?: boolean;
  done?: boolean;
};

export function BookingSteps({ steps }: { steps: BookingStep[] }) {
  return (
    <div className="flex items-center gap-3 text-sm mb-2">
      {steps.map((s, i) => (
        <div key={s.key} className="flex items-center gap-3">
          <div
            className={cn(
              'px-2 py-1 rounded border',
              s.active ? 'border-[#00D4AA] text-[#00D4AA]' : s.done ? 'border-neutral-600 text-neutral-300' : 'border-neutral-800 text-neutral-500'
            )}
          >
            {s.label}
          </div>
          {i < steps.length - 1 && <div className="w-6 h-px bg-neutral-700" />}
        </div>
      ))}
    </div>
  );
}

