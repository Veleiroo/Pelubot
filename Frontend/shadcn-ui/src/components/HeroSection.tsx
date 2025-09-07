import { Button } from '@/components/ui/button';
import { Scissors, Star } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function HeroSection() {
    const navigate = useNavigate();

    const handleReservation = () => {
        navigate('/book/service');
    };

    const scrollToContact = () => {
        const element = document.getElementById('contacto');
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };

    return (
        <section id="inicio" className="relative min-h-screen flex items-center justify-center overflow-hidden">
            {/* Background Image */}
            <div
                className="absolute inset-0 bg-cover bg-center bg-no-repeat"
                style={{
                    backgroundImage: 'url(/assets/barber-tools.jpg)',
                }}
            >
                <div className="absolute inset-0 bg-black/70"></div>
            </div>

            {/* Content */}
            <div className="relative z-10 text-center px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
                <div className="flex items-center justify-center mb-6">
                    <Scissors className="text-[#00D4AA] mr-3" size={48} />
                    <div className="flex">
                        {[...Array(5)].map((_, i) => (
                            <Star key={i} className="text-[#00D4AA] fill-current" size={24} />
                        ))}
                    </div>
                </div>

                <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
                    <span className="text-[#00D4AA]">DEINIS</span>
                    <br />
                    BARBER CLUB
                </h1>

                <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-2xl mx-auto leading-relaxed">
                    Donde el estilo urbano se encuentra con la tradición.
                    Cortes profesionales, ambiente único, experiencia inolvidable.
                </p>

                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                    <Button
                        onClick={handleReservation}
                        size="lg"
                        className="bg-[#00D4AA] hover:bg-[#00B894] text-black font-bold text-lg px-8 py-4 transition-all duration-300 transform hover:scale-105"
                    >
                        RESERVA TU CITA
                    </Button>
                    <Button
                        onClick={scrollToContact}
                        variant="outline"
                        size="lg"
                        className="border-[#00D4AA] text-[#00D4AA] hover:bg-[#00D4AA] hover:text-black font-bold text-lg px-8 py-4 transition-all duration-300"
                    >
                        VER HORARIOS
                    </Button>
                </div>

                {/* Floating Elements */}
                <div className="absolute top-20 left-10 animate-pulse">
                    <div className="w-2 h-2 bg-[#00D4AA] rounded-full"></div>
                </div>
                <div className="absolute bottom-20 right-10 animate-pulse delay-1000">
                    <div className="w-3 h-3 bg-[#00D4AA] rounded-full"></div>
                </div>
            </div>

            {/* Scroll Indicator */}
            <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
                <div className="w-6 h-10 border-2 border-[#00D4AA] rounded-full flex justify-center">
                    <div className="w-1 h-3 bg-[#00D4AA] rounded-full mt-2 animate-pulse"></div>
                </div>
            </div>
        </section>
    );
}
