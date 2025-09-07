import { Scissors, Instagram, Facebook, Twitter, MapPin, Phone, Mail } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  const handleSocialClick = (platform: string) => {
    const urls = {
      instagram: 'https://instagram.com/deinisbarberclub',
      facebook: 'https://facebook.com/deinisbarberclub',
      twitter: 'https://twitter.com/deinisbarberclub'
    };
    window.open(urls[platform as keyof typeof urls], '_blank');
  };

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <footer className="bg-[#0a0a0a] border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center mb-4">
              <Scissors className="text-[#00D4AA] mr-3" size={32} />
              <h3 className="text-2xl font-bold text-white">
                <span className="text-[#00D4AA]">Deinis</span> Barber Club
              </h3>
            </div>
            <p className="text-gray-400 mb-6 max-w-md leading-relaxed">
              Donde el estilo urbano se encuentra con la tradición. Más que una barbería, 
              somos tu destino para lucir siempre impecable.
            </p>
            
            {/* Social Media */}
            <div className="flex space-x-4">
              <button
                onClick={() => handleSocialClick('instagram')}
                className="p-3 bg-[#1a1a1a] hover:bg-[#00D4AA] text-gray-400 hover:text-black rounded-lg transition-all duration-300"
              >
                <Instagram size={20} />
              </button>
              <button
                onClick={() => handleSocialClick('facebook')}
                className="p-3 bg-[#1a1a1a] hover:bg-[#00D4AA] text-gray-400 hover:text-black rounded-lg transition-all duration-300"
              >
                <Facebook size={20} />
              </button>
              <button
                onClick={() => handleSocialClick('twitter')}
                className="p-3 bg-[#1a1a1a] hover:bg-[#00D4AA] text-gray-400 hover:text-black rounded-lg transition-all duration-300"
              >
                <Twitter size={20} />
              </button>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Enlaces Rápidos</h4>
            <ul className="space-y-3">
              <li>
                <button
                  onClick={() => scrollToSection('inicio')}
                  className="text-gray-400 hover:text-[#00D4AA] transition-colors"
                >
                  Inicio
                </button>
              </li>
              <li>
                <button
                  onClick={() => scrollToSection('sobre-nosotros')}
                  className="text-gray-400 hover:text-[#00D4AA] transition-colors"
                >
                  Sobre Nosotros
                </button>
              </li>
              <li>
                <button
                  onClick={() => scrollToSection('servicios')}
                  className="text-gray-400 hover:text-[#00D4AA] transition-colors"
                >
                  Servicios
                </button>
              </li>
              <li>
                <button
                  onClick={() => scrollToSection('galeria')}
                  className="text-gray-400 hover:text-[#00D4AA] transition-colors"
                >
                  Galería
                </button>
              </li>
              <li>
                <button
                  onClick={() => scrollToSection('contacto')}
                  className="text-gray-400 hover:text-[#00D4AA] transition-colors"
                >
                  Contacto
                </button>
              </li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h4 className="text-white font-semibold mb-4">Contacto</h4>
            <ul className="space-y-3">
              <li className="flex items-start space-x-3">
                <MapPin className="text-[#00D4AA] mt-1 flex-shrink-0" size={16} />
                <span className="text-gray-400 text-sm">
                  Calle Principal 123<br />
                  28001 Madrid, España
                </span>
              </li>
              <li className="flex items-center space-x-3">
                <Phone className="text-[#00D4AA] flex-shrink-0" size={16} />
                <span className="text-gray-400 text-sm">+34 123 456 789</span>
              </li>
              <li className="flex items-center space-x-3">
                <Mail className="text-[#00D4AA] flex-shrink-0" size={16} />
                <span className="text-gray-400 text-sm">info@deinisbarberclub.com</span>
              </li>
            </ul>

            <div className="mt-6 p-4 bg-[#1a1a1a] rounded-lg border border-gray-800">
              <p className="text-[#00D4AA] text-sm font-semibold mb-1">Horario de Atención</p>
              <p className="text-gray-400 text-xs">Lun-Vie: 9:00-20:00</p>
              <p className="text-gray-400 text-xs">Sáb: 9:00-18:00 | Dom: 10:00-16:00</p>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-800 mt-12 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm mb-4 md:mb-0">
              © {currentYear} Deinis Barber Club. Todos los derechos reservados.
            </p>
            <div className="flex space-x-6 text-sm">
              <a href="#" className="text-gray-400 hover:text-[#00D4AA] transition-colors">
                Política de Privacidad
              </a>
              <a href="#" className="text-gray-400 hover:text-[#00D4AA] transition-colors">
                Términos de Servicio
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Floating WhatsApp Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => window.open('https://wa.me/1234567890?text=Hola, me gustaría reservar una cita en Deinis Barber Club', '_blank')}
          className="bg-[#25D366] hover:bg-[#20BA5A] text-white p-4 rounded-full shadow-lg transition-all duration-300 transform hover:scale-110"
          aria-label="Contactar por WhatsApp"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.465 3.085"/>
          </svg>
        </button>
      </div>
    </footer>
  );
}