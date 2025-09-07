import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Index from '@/pages/Index';
import NotFound from '@/pages/NotFound';
import BookService from '@/pages/book/Service';
import BookDate from '@/pages/book/Date';
import BookTime from '@/pages/book/Time';
import BookDetails from '@/pages/book/Details';
import BookConfirm from '@/pages/book/Confirm';

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

                    <Route path="*" element={<NotFound />} />
                </Routes>
            </BrowserRouter>
        </TooltipProvider>
    </QueryClientProvider>
);

export default App;
