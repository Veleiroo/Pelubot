import { useMemo, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { addDays, addMonths, endOfMonth, endOfWeek, format, isAfter, isBefore, isSameDay, isSameMonth, isToday, startOfMonth, startOfWeek } from 'date-fns';
import { es } from 'date-fns/locale';

const toYmd = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
};

/**
 * Vista de previsualización del calendario para validar maquetación sin API.
 */
export default function CalendarPreview() {
  const [month, setMonth] = useState<Date>(() => new Date());
  const [selected, setSelected] = useState<Date | undefined>(undefined);
  const [focusedDate, setFocusedDate] = useState<Date>(() => new Date());

  // Mock de días disponibles: fines de semana no y cada 2 días sí
  const avail = useMemo(() => {
    const s = new Set<string>();
    const ms = startOfMonth(month); const me = endOfMonth(month);
    let d = ms;
    while (d <= me) {
      const wd = d.getDay(); // 0=Dom
      if (wd !== 0 && wd !== 6 && d.getDate() % 2 === 0) s.add(toYmd(d));
      d = addDays(d, 1);
    }
    return s;
  }, [month]);

  const today = useMemo(() => {
    const t = new Date(); t.setHours(0,0,0,0); return t;
  }, []);
  const maxDate = useMemo(() => { const d = new Date(today); d.setMonth(d.getMonth()+6); return d; }, [today]);

  const monthStart = useMemo(() => startOfMonth(month), [month]);
  const monthEnd = useMemo(() => endOfMonth(month), [month]);
  const gridStart = useMemo(() => startOfWeek(monthStart, { weekStartsOn: 1 }), [monthStart]);
  const gridEnd = useMemo(() => endOfWeek(monthEnd, { weekStartsOn: 1 }), [monthEnd]);
  const days = useMemo(() => {
    const list: Date[] = []; let d = gridStart; while (d <= gridEnd) { list.push(d); d = addDays(d, 1); } return list;
  }, [gridStart, gridEnd]);

  const onPrevMonth = () => setMonth(addMonths(month, -1));
  const onNextMonth = () => setMonth(addMonths(month, 1));

  const onGridKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    const key = e.key; let next = focusedDate || today;
    if (key === 'ArrowLeft') { next = addDays(next, -1); e.preventDefault(); }
    else if (key === 'ArrowRight') { next = addDays(next, 1); e.preventDefault(); }
    else if (key === 'ArrowUp') { next = addDays(next, -7); e.preventDefault(); }
    else if (key === 'ArrowDown') { next = addDays(next, 7); e.preventDefault(); }
    else if (key === 'PageUp') { next = addMonths(next, -1); e.preventDefault(); }
    else if (key === 'PageDown') { next = addMonths(next, 1); e.preventDefault(); }
    else if (key === 'Enter' || key === ' ') {
      const ymd = toYmd(focusedDate);
      const enabled = isSameMonth(focusedDate, month) && !isBefore(focusedDate, today) && !isAfter(focusedDate, maxDate) && avail.has(ymd);
      if (enabled) setSelected(focusedDate);
      return;
    } else return;
    if (next.getMonth() !== month.getMonth() || next.getFullYear() !== month.getFullYear()) setMonth(new Date(next.getFullYear(), next.getMonth(), 1));
    setFocusedDate(next);
  }, [focusedDate, today, maxDate, month, avail]);

  return (
    <div className="mx-auto max-w-4xl p-6 text-white space-y-6">
      <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6 w-full max-w-[420px] mx-auto">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold">{format(month, 'LLLL yyyy', { locale: es })}</h2>
            <p className="text-sm text-muted-foreground">Elige un día disponible</p>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" onClick={onPrevMonth} aria-label="Mes anterior"><ChevronLeft className="h-4 w-4" /></Button>
            <Button variant="ghost" size="icon" onClick={onNextMonth} aria-label="Mes siguiente"><ChevronRight className="h-4 w-4" /></Button>
          </div>
        </div>
        <div className="grid grid-cols-7 gap-1 mb-1 text-xs text-muted-foreground">
          {['L','M','X','J','V','S','D'].map((w) => (<div key={w} className="h-8 flex items-center justify-center">{w}</div>))}
        </div>
        <div role="grid" aria-label={format(month, 'LLLL yyyy', { locale: es })} className="grid grid-cols-7 gap-1" tabIndex={0} onKeyDown={onGridKeyDown}>
          {days.map((d) => {
            const ymd = toYmd(d);
            const inMonth = isSameMonth(d, month);
            const outOfRange = isBefore(d, today) || isAfter(d, maxDate);
            const enabled = inMonth && !outOfRange && avail.has(ymd);
            const selectedDay = selected ? isSameDay(d, selected) : false;
            const classes = [
              'aspect-square flex items-center justify-center rounded-md text-sm transition-colors duration-150',
              '[font-variant-numeric:tabular-nums]',
              isToday(d) ? 'ring-1 ring-foreground/15' : '',
              !inMonth ? 'text-muted-foreground/60 cursor-not-allowed' : (
                enabled ? (selectedDay ? 'bg-emerald-500 text-emerald-950' : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500') : 'text-muted-foreground/60 cursor-not-allowed'
              )
            ].filter(Boolean).join(' ');
            return (
              <button key={ymd} type="button" role="gridcell" aria-selected={selectedDay} aria-disabled={!enabled} disabled={!enabled} className={classes}>
                {String(d.getDate())}
              </button>
            );
          })}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">Días en verde = hay disponibilidad para el servicio elegido.</p>
      </div>
    </div>
  );
}

