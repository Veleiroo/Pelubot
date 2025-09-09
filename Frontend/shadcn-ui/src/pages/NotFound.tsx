import { Button } from '@/components/ui/button';
import React, { Suspense, lazy } from 'react';

const DebugPage = lazy(() => import('./Debug'));

export default function NotFoundPage() {
  // Fallback para debug: si el usuario navega a /debug y por alguna razón
  // el router no tiene la ruta, mostramos la página de debug desde aquí.
  if (typeof window !== 'undefined' && window.location) {
    const loc = window.location;
    const s = (loc.pathname || '') + (loc.search || '') + (loc.hash || '');
    if (/debug/i.test(s)) {
      return (
        <Suspense fallback={<div style={{ padding: 16 }}>Cargando debug…</div>}>
          <DebugPage />
        </Suspense>
      );
    }
  }
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-black p-6 text-center text-white">
      <div className="space-y-6 max-w-md">
        <div className="space-y-3">
          <h1 className="text-8xl font-bold text-[#00D4AA]">404</h1>
          <h2 className="text-2xl font-semibold">Página no encontrada</h2>
          <p className="text-neutral-400">La página solicitada no existe o pudo haberse movido.</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild>
            <a href="/">Volver al inicio</a>
          </Button>
          <Button variant="outline" onClick={() => window.history.back()}>
            Volver atrás
          </Button>
        </div>
      </div>
    </div>
  );
}
