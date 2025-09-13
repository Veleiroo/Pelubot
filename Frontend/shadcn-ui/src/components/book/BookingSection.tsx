import { ReactNode } from 'react';

export function BookingSection({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <section className="mx-auto w-full max-w-4xl px-6 sm:px-8">
      <header className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold">{title}</h1>
        {subtitle ? <p className="text-sm text-muted-foreground">{subtitle}</p> : null}
      </header>
      <div className="space-y-6">{children}</div>
    </section>
  );
}

export default BookingSection;

