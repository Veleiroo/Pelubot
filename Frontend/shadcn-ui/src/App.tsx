import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Index from '@/pages/Index';
import NotFound from '@/pages/NotFound';
const BookService = lazy(() => import('@/pages/book/Service'));
import BookDate from '@/pages/book/Date';
const BookTime = lazy(() => import('@/pages/book/Time'));
const BookDetails = lazy(() => import('@/pages/book/Details'));
const BookConfirm = lazy(() => import('@/pages/book/Confirm'));
import { ErrorBoundary } from '@/components/ErrorBoundary';
const DEBUG = String(import.meta.env.VITE_ENABLE_DEBUG ?? '0') === '1' || String(import.meta.env.VITE_ENABLE_DEBUG ?? '').toLowerCase() === 'true';
const DebugPage = lazy(() => import('./pages/Debug'));

const queryClient = new QueryClient();

const App = () => (
    <QueryClientProvider client={queryClient}>
        <TooltipProvider>
            <Toaster />
            <BrowserRouter>
                <ErrorBoundary>
                <Routes>
                    <Route path="/" element={<Index />} />

                    {/* Flujo de reservas. */}
                    <Route path="/book/service" element={<Suspense fallback={<div style={{ padding: 16 }}>Cargando servicios…</div>}><BookService /></Suspense>} />
                    <Route path="/book/date" element={<BookDate />} />
                    <Route path="/book/time" element={<Suspense fallback={<div style={{ padding: 16 }}>Cargando horarios…</div>}><BookTime /></Suspense>} />
                    <Route path="/book/details" element={<Suspense fallback={<div style={{ padding: 16 }}>Cargando…</div>}><BookDetails /></Suspense>} />
                    <Route path="/book/confirm" element={<Suspense fallback={<div style={{ padding: 16 }}>Cargando confirmación…</div>}><BookConfirm /></Suspense>} />
                    <Route
                        path="/debug"
                        element={
                            <Suspense fallback={<div style={{ padding: 16 }}>Cargando debug…</div>}>
                                <DebugPage />
                            </Suspense>
                        }
                    />

                    <Route path="*" element={<NotFound />} />
                </Routes>
                </ErrorBoundary>
            </BrowserRouter>
        </TooltipProvider>
    </QueryClientProvider>
);

export default App;
