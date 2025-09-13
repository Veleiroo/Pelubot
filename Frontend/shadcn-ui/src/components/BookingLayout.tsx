import { ReactNode } from 'react';
import { BookingSteps, BookingStep } from '@/components/BookingSteps';

interface BookingLayoutProps {
  steps: BookingStep[];
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function BookingLayout({ steps, title, subtitle, children }: BookingLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-900/20 via-slate-900/5 to-transparent"></div>
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:60px_60px]"></div>

      <div className="relative mx-auto max-w-5xl p-6 text-white space-y-8">
        <BookingSteps steps={steps} />

        <div className="text-center space-y-4 animate-in fade-in-50 slide-in-from-top-4 duration-700">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-emerald-500/10 to-blue-500/10 border border-emerald-500/20 backdrop-blur-sm">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-emerald-300">Reserva Online</span>
          </div>

          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-emerald-200 to-emerald-400 bg-clip-text text-transparent leading-tight">
            {title}
          </h1>

          {subtitle && (
            <p className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
              {subtitle}
            </p>
          )}
        </div>

        <div className="animate-in fade-in-50 slide-in-from-bottom-4 duration-700 delay-200">
          {children}
        </div>
      </div>
    </div>
  );
}

export default BookingLayout;

