import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Index from '@/pages/Index';
import NotFound from '@/pages/NotFound';
import BookService from '@/pages/book/Service';
import BookDate from '@/pages/book/Date';
import BookTime from '@/pages/book/Time';
import BookDetails from '@/pages/book/Details';
import BookConfirm from '@/pages/book/Confirm';
const DEBUG = String(import.meta.env.VITE_ENABLE_DEBUG ?? '0') === '1' || String(import.meta.env.VITE_ENABLE_DEBUG ?? '').toLowerCase() === 'true';
const DebugPage = lazy(() => import('./pages/Debug'));

const queryClient = new QueryClient();

const App = () => (
    <QueryClientProvider client={queryClient}>
        <TooltipProvider>
            <Toaster />
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Index />} />

                    {/* Flujo de reservas. */}
                    <Route path="/book/service" element={<BookService />} />
                    <Route path="/book/date" element={<BookDate />} />
                    <Route path="/book/time" element={<BookTime />} />
                    <Route path="/book/details" element={<BookDetails />} />
                    <Route path="/book/confirm" element={<BookConfirm />} />
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
            </BrowserRouter>
        </TooltipProvider>
    </QueryClientProvider>
);

export default App;
