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
    <div className="mx-auto max-w-4xl p-6 text-white space-y-6">
      <BookingSteps steps={steps} />
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">{title}</h1>
        {subtitle && <p className="text-neutral-400">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export default BookingLayout;
