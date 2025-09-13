import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export interface CalendarNavProps {
  month: Date;
  onPrev: () => void;
  onNext: () => void;
}

/**
 * Cabecera de calendario con título del mes y navegación.
 * Props:
 *  - month: Date actual mostrado
 *  - onPrev: handler para ir al mes anterior
 *  - onNext: handler para ir al mes siguiente
 */
export function CalendarNav({ month, onPrev, onNext }: CalendarNavProps) {
  return (
    <div className="flex items-center justify-between mb-3">
      <div>
        <h2 className="text-base font-medium">{format(month, 'LLLL yyyy', { locale: es })}</h2>
        <p className="text-xs text-muted-foreground">Elige un día disponible</p>
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" onClick={onPrev} aria-label="Mes anterior">
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={onNext} aria-label="Mes siguiente">
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export default CalendarNav;
