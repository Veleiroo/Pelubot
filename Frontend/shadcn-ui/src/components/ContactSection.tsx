import { MapPin, Phone, Clock, Mail, MessageCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

export default function ContactSection() {
  const navigate = useNavigate();
  const handleWhatsApp = () => {
    navigate('/book/service');
  };

  const handleCall = () => {
    window.open('tel:+34123456789', '_self');
  };

  const handleEmail = () => {
    window.open('mailto:info@deinisbarberclub.com', '_self');
  };

  return (
    <section id="contacto" className="py-20 bg-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            <span className="text-brand">Contacto</span> & Ubicación
          </h2>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            Estamos aquí para ti. Reserva tu cita o visítanos en nuestro local. 
            Tu nuevo look te está esperando.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Contact Info */}
          <div className="space-y-8">
            <div className="bg-[#1a1a1a] border border-gray-800 rounded-lg p-8">
              <h3 className="text-2xl font-bold text-white mb-6">Información de Contacto</h3>
              
              <div className="space-y-6">
                <div className="flex items-start space-x-4">
                  <div className="p-3 bg-brand/10 rounded-lg">
                    <MapPin className="text-brand" size={24} />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-1">Dirección</h4>
                    <p className="text-gray-400">
                      Calle Principal 123<br />
                      28001 Madrid, España
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="p-3 bg-brand/10 rounded-lg">
                    <Phone className="text-brand" size={24} />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-1">Teléfono</h4>
                    <p className="text-gray-400">+34 123 456 789</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="p-3 bg-brand/10 rounded-lg">
                    <Mail className="text-brand" size={24} />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-1">Email</h4>
                    <p className="text-gray-400">info@deinisbarberclub.com</p>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 mt-8">
                <Button
                  onClick={handleWhatsApp}
                  className="bg-brand hover:bg-[#00B894] text-black font-semibold flex items-center justify-center"
                >
                  <MessageCircle className="mr-2" size={20} />
                  WhatsApp
                </Button>
                <Button
                  onClick={handleCall}
                  variant="outline"
                  className="border-brand text-brand hover:bg-brand hover:text-black flex items-center justify-center"
                >
                  <Phone className="mr-2" size={20} />
                  Llamar
                </Button>
              </div>
            </div>

            {/* Hours */}
            <div className="bg-[#1a1a1a] border border-gray-800 rounded-lg p-8">
              <div className="flex items-center mb-6">
                <Clock className="text-brand mr-3" size={24} />
                <h3 className="text-2xl font-bold text-white">Horarios</h3>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-gray-800">
                  <span className="text-gray-300">Lunes - Viernes</span>
                  <span className="text-white font-semibold">9:00 - 20:00</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-800">
                  <span className="text-gray-300">Sábados</span>
                  <span className="text-white font-semibold">9:00 - 18:00</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-300">Domingos</span>
                  <span className="text-brand font-semibold">10:00 - 16:00</span>
                </div>
              </div>

              <div className="mt-6 p-4 bg-brand/10 rounded-lg border border-brand/20">
                <p className="text-brand text-sm font-semibold">
                  💡 Consejo: Reserva con anticipación para garantizar tu horario preferido
                </p>
              </div>
            </div>
          </div>

          {/* Map/Image */}
          <div className="space-y-6">
            <div className="bg-[#1a1a1a] border border-gray-800 rounded-lg p-8 h-full">
              <h3 className="text-2xl font-bold text-white mb-6">Nuestro Local</h3>
              
              {/* Placeholder for map - you can replace with actual map */}
              <div className="bg-gray-800 rounded-lg h-64 flex items-center justify-center mb-6">
                <div className="text-center">
                  <MapPin className="text-brand mx-auto mb-2" size={48} />
                  <p className="text-gray-400">Mapa Interactivo</p>
                  <p className="text-gray-500 text-sm">Calle Principal 123, Madrid</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center text-gray-300">
                  <div className="w-2 h-2 bg-brand rounded-full mr-3"></div>
                  Fácil acceso en transporte público
                </div>
                <div className="flex items-center text-gray-300">
                  <div className="w-2 h-2 bg-brand rounded-full mr-3"></div>
                  Parking disponible en la zona
                </div>
                <div className="flex items-center text-gray-300">
                  <div className="w-2 h-2 bg-brand rounded-full mr-3"></div>
                  Ambiente moderno y acogedor
                </div>
                <div className="flex items-center text-gray-300">
                  <div className="w-2 h-2 bg-brand rounded-full mr-3"></div>
                  Equipamiento de última generación
                </div>
              </div>

              <Button
                onClick={handleWhatsApp}
                size="lg"
                className="w-full mt-8 bg-brand hover:bg-[#00B894] text-black font-bold"
              >
                RESERVAR CITA AHORA
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
