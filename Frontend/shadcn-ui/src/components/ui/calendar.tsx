import * as React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { DayPicker } from 'react-day-picker';
import { es as esLocale } from 'date-fns/locale';
import type { Locale } from 'date-fns';

import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';

export type CalendarProps = React.ComponentProps<typeof DayPicker>;

function Calendar({ className, classNames, showOutsideDays = true, locale, ...props }: CalendarProps) {
  // Usar español con lunes como primer día.
  const loc = React.useMemo(() => {
    const base: Locale = locale ?? esLocale;
    return { ...base, options: { ...(base.options || {}), weekStartsOn: 1 } } as Locale;
  }, [locale]);

  // Límite de navegación: hoy .. hoy + 183 días (≈6 meses).
  const today = React.useMemo(() => new Date(), []);
  const toMonthDefault = React.useMemo(() => {
    const d = new Date();
    d.setDate(d.getDate() + 183);
    return d;
  }, []);
  const fromMonth = props.fromMonth ?? today;
  const toMonth = props.toMonth ?? toMonthDefault;

  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      locale={loc}
      fromMonth={fromMonth}
      toMonth={toMonth}
      className={cn('pelu-cal p-2', className)}
      classNames={{
        months: 'flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0',
        month: 'space-y-3',
        caption: 'flex justify-center pt-1 relative items-center',
        caption_label: 'text-sm font-medium text-neutral-100',
        nav: 'space-x-1 flex items-center',
        nav_button: cn(
          buttonVariants({ variant: 'ghost' }),
          'h-7 w-7 p-0 text-neutral-100 hover:bg-neutral-800 hover:text-white'
        ),
        nav_button_previous: 'absolute left-1',
        nav_button_next: 'absolute right-1',
        table: 'w-full border-collapse table-fixed',
        head_row: '',
        head_cell: 'text-muted-foreground h-8 text-[0.72rem] uppercase tracking-wide text-center',
        row: '',
        cell: 'p-0 text-center align-middle',
        // Celda ligera y botón de día centrado para no romper columnas.
        day: 'p-0 text-center align-middle',
        day_button: cn(buttonVariants({ variant: 'ghost' }), 'h-9 w-9 p-0 font-normal aria-selected:opacity-100 inline-flex items-center justify-center mx-auto'),
        day_range_end: 'day-range-end',
        day_selected:
          'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground',
        day_today: 'bg-accent text-accent-foreground',
        day_outside:
          'day-outside text-muted-foreground opacity-50 aria-selected:bg-accent/50 aria-selected:text-muted-foreground aria-selected:opacity-30',
        day_disabled: 'text-muted-foreground opacity-50',
        day_range_middle: 'aria-selected:bg-accent aria-selected:text-accent-foreground',
        day_hidden: 'invisible',
        ...classNames,
      }}
      components={{
        IconLeft: ({ ..._props }) => <ChevronLeft className="h-4 w-4" />,
        IconRight: ({ ..._props }) => <ChevronRight className="h-4 w-4" />,
      }}
      {...props}
    />
  );
}
Calendar.displayName = 'Calendar';

export { Calendar };
