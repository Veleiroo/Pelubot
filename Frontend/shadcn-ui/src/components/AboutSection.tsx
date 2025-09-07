import { Award, Users, Clock, Scissors } from 'lucide-react';

export default function AboutSection() {
  return (
    <section id="sobre-nosotros" className="py-20 bg-[#1a1a1a]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Image */}
          <div className="relative">
            <div className="relative overflow-hidden rounded-lg">
              <img
                src="/assets/barber-working.jpg"
                alt="Deinis trabajando"
                className="w-full h-[600px] object-cover transition-transform duration-500 hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
            </div>
            <div className="absolute -bottom-6 -right-6 bg-[#00D4AA] text-black p-6 rounded-lg font-bold text-lg">
              +5 Años de Experiencia
            </div>
          </div>

          {/* Content */}
          <div className="space-y-8">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                Sobre <span className="text-[#00D4AA]">Nosotros</span>
              </h2>
              <p className="text-gray-300 text-lg leading-relaxed mb-6">
                En Deinis Barber Club, combinamos la tradición de la barbería clásica con el estilo urbano contemporáneo. 
                Nuestro compromiso es ofrecer no solo un corte de cabello, sino una experiencia completa que refleje tu personalidad única.
              </p>
              <p className="text-gray-300 text-lg leading-relaxed">
                Con años de experiencia y una pasión genuina por nuestro oficio, creamos looks que van desde lo clásico 
                hasta lo más vanguardista, siempre con la máxima atención al detalle.
              </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center p-6 bg-black/50 rounded-lg border border-gray-800">
                <Users className="text-[#00D4AA] mx-auto mb-3" size={32} />
                <div className="text-3xl font-bold text-white mb-1">500+</div>
                <div className="text-gray-400">Clientes Satisfechos</div>
              </div>
              <div className="text-center p-6 bg-black/50 rounded-lg border border-gray-800">
                <Award className="text-[#00D4AA] mx-auto mb-3" size={32} />
                <div className="text-3xl font-bold text-white mb-1">5★</div>
                <div className="text-gray-400">Calificación Promedio</div>
              </div>
              <div className="text-center p-6 bg-black/50 rounded-lg border border-gray-800">
                <Clock className="text-[#00D4AA] mx-auto mb-3" size={32} />
                <div className="text-3xl font-bold text-white mb-1">7</div>
                <div className="text-gray-400">Días a la Semana</div>
              </div>
              <div className="text-center p-6 bg-black/50 rounded-lg border border-gray-800">
                <Scissors className="text-[#00D4AA] mx-auto mb-3" size={32} />
                <div className="text-3xl font-bold text-white mb-1">100%</div>
                <div className="text-gray-400">Profesional</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}