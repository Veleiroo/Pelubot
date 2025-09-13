import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Index from '@/pages/Index';
import NotFound from '@/pages/NotFound';
const BookService = lazy(() => import('@/pages/book/Service'));
import BookDate from '@/pages/book/Date';
const BookDetails = lazy(() => import('@/pages/book/Details'));
const BookConfirm = lazy(() => import('@/pages/book/Confirm'));
import Loading from '@/components/Loading';
import { ErrorBoundary } from '@/components/ErrorBoundary';
const DEBUG =
  String(import.meta.env.VITE_ENABLE_DEBUG ?? '0') === '1' ||
  String(import.meta.env.VITE_ENABLE_DEBUG ?? '').toLowerCase() === 'true';
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
                    <Route
                        path="/book/service"
                        element={
                            <Suspense fallback={<Loading />}>
                                <BookService />
                            </Suspense>
                        }
                    />
                    <Route path="/book/date" element={<BookDate />} />
                    {/** Ruta /book/time eliminada: flujo es Service -> Date -> Confirm */}
                    <Route
                        path="/book/details"
                        element={
                            <Suspense fallback={<Loading />}>
                                <BookDetails />
                            </Suspense>
                        }
                    />
                    <Route
                        path="/book/confirm"
                        element={
                            <Suspense fallback={<Loading />}>
                                <BookConfirm />
                            </Suspense>
                        }
                    />
                    <Route
                        path="/debug"
                        element={
                            <Suspense fallback={<Loading />}>
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
