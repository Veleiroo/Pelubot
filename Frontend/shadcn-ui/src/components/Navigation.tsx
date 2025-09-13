import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Menu, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Navigation() {
    const [isOpen, setIsOpen] = useState(false);
    const navigate = useNavigate();

    const scrollToSection = (sectionId: string) => {
        const element = document.getElementById(sectionId);
        if (element) element.scrollIntoView({ behavior: 'smooth' });
        setIsOpen(false);
    };

    const handleReservation = () => {
        navigate('/book/service');
    };

    return (
        <nav className="fixed top-0 w-full bg-black/90 backdrop-blur-sm z-50 border-b border-gray-800">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                    <div className="flex-shrink-0">
                        <h1 className="text-2xl font-bold text-white">
                            <span className="text-brand">Deinis</span> Barber Club
                        </h1>
                    </div>

                    {/* Desktop Navigation */}
                    <div className="hidden md:block">
                        <div className="ml-10 flex items-baseline space-x-4">
                            <button
                                onClick={() => scrollToSection('inicio')}
                                className="text-gray-300 hover:text-brand px-3 py-2 text-sm font-medium transition-colors"
                            >
                                Inicio
                            </button>
                            <button
                                onClick={() => scrollToSection('sobre-nosotros')}
                                className="text-gray-300 hover:text-brand px-3 py-2 text-sm font-medium transition-colors"
                            >
                                Sobre Nosotros
                            </button>
                            <button
                                onClick={() => scrollToSection('servicios')}
                                className="text-gray-300 hover:text-brand px-3 py-2 text-sm font-medium transition-colors"
                            >
                                Servicios
                            </button>
                            <button
                                onClick={() => scrollToSection('galeria')}
                                className="text-gray-300 hover:text-brand px-3 py-2 text-sm font-medium transition-colors"
                            >
                                Galería
                            </button>
                            <button
                                onClick={() => scrollToSection('contacto')}
                                className="text-gray-300 hover:text-brand px-3 py-2 text-sm font-medium transition-colors"
                            >
                                Contacto
                            </button>
                            <Button
                                onClick={handleReservation}
                                className="bg-brand hover:bg-[#00B894] text-black font-semibold ml-4"
                            >
                                Reserva tu Cita
                            </Button>
                        </div>
                    </div>

                    {/* Mobile menu button */}
                    <div className="md:hidden">
                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            className="text-gray-300 hover:text-white p-2"
                            aria-label="Abrir menú"
                            aria-expanded={isOpen}
                        >
                            {isOpen ? <X size={24} /> : <Menu size={24} />}
                        </button>
                    </div>
                </div>

                {/* Mobile Navigation */}
                {isOpen && (
                    <div className="md:hidden">
                        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-black/95">
                            <button
                                onClick={() => scrollToSection('inicio')}
                                className="text-gray-300 hover:text-brand block px-3 py-2 text-base font-medium w-full text-left transition-colors"
                            >
                                Inicio
                            </button>
                            <button
                                onClick={() => scrollToSection('sobre-nosotros')}
                                className="text-gray-300 hover:text-brand block px-3 py-2 text-base font-medium w-full text-left transition-colors"
                            >
                                Sobre Nosotros
                            </button>
                            <button
                                onClick={() => scrollToSection('servicios')}
                                className="text-gray-300 hover:text-brand block px-3 py-2 text-base font-medium w-full text-left transition-colors"
                            >
                                Servicios
                            </button>
                            <button
                                onClick={() => scrollToSection('galeria')}
                                className="text-gray-300 hover:text-brand block px-3 py-2 text-base font-medium w-full text-left transition-colors"
                            >
                                Galería
                            </button>
                            <button
                                onClick={() => scrollToSection('contacto')}
                                className="text-gray-300 hover:text-brand block px-3 py-2 text-base font-medium w-full text-left transition-colors"
                            >
                                Contacto
                            </button>
                            <Button
                                onClick={() => { setIsOpen(false); handleReservation(); }}
                                className="bg-brand hover:bg-[#00B894] text-black font-semibold w-full mt-4"
                            >
                                Reserva tu Cita
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </nav>
    );
}
