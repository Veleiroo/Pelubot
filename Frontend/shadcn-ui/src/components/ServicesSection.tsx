import { Scissors, Zap, Sparkles, Crown, Brush, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

export default function ServicesSection() {
  const navigate = useNavigate();
  const services = [
    {
      icon: <Scissors className="text-brand" size={32} />,
      title: "Corte Clásico",
      description: "Cortes tradicionales con técnicas modernas. Perfecto para el hombre elegante.",
      price: "€25",
      features: ["Lavado incluido", "Peinado", "Consulta personalizada"]
    },
    {
      icon: <Zap className="text-brand" size={32} />,
      title: "Afeitado Premium",
      description: "Afeitado tradicional con navaja. Una experiencia de lujo incomparable.",
      price: "€20",
      features: ["Toallas calientes", "Aceites premium", "Masaje facial"]
    },
    {
      icon: <Crown className="text-brand" size={32} />,
      title: "Corte + Barba",
      description: "El combo perfecto. Corte de cabello y arreglo de barba profesional.",
      price: "€35",
      features: ["Diseño de barba", "Productos premium", "Acabado perfecto"]
    },
    {
      icon: <Sparkles className="text-brand" size={32} />,
      title: "Tratamiento Capilar",
      description: "Cuidado especializado para tu cabello. Nutrición y fortalecimiento.",
      price: "€30",
      features: ["Análisis capilar", "Mascarilla nutritiva", "Masaje relajante"]
    },
    {
      icon: <Brush className="text-brand" size={32} />,
      title: "Peinado Especial",
      description: "Para eventos especiales. Looks únicos para ocasiones importantes.",
      price: "€15",
      features: ["Consulta de estilo", "Productos de fijación", "Retoque gratuito"]
    },
    {
      icon: <Star className="text-brand" size={32} />,
      title: "Experiencia VIP",
      description: "El servicio completo. Todo lo que necesitas en una sola sesión.",
      price: "€60",
      features: ["Todos los servicios", "Bebida incluida", "Atención personalizada"]
    }
  ];

  const handleReservation = () => {
    navigate('/book/service');
  };

  return (
    <section id="servicios" className="py-20 bg-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Nuestros <span className="text-brand">Servicios</span>
          </h2>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            Ofrecemos una gama completa de servicios profesionales para el cuidado masculino, 
            desde cortes clásicos hasta tratamientos especializados.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {services.map((service, index) => (
            <div
              key={index}
              className="bg-[#1a1a1a] border border-gray-800 rounded-lg p-8 hover:border-brand transition-all duration-300 group hover:transform hover:scale-105"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="p-3 bg-black rounded-lg group-hover:bg-brand/10 transition-colors">
                  {service.icon}
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-brand">{service.price}</div>
                </div>
              </div>

              <h3 className="text-xl font-bold text-white mb-3">{service.title}</h3>
              <p className="text-gray-400 mb-6 leading-relaxed">{service.description}</p>

              <ul className="space-y-2 mb-6">
                {service.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-center text-gray-300">
                    <div className="w-2 h-2 bg-brand rounded-full mr-3"></div>
                    {feature}
                  </li>
                ))}
              </ul>

              <Button
                onClick={handleReservation}
                className="w-full bg-transparent border border-brand text-brand hover:bg-brand hover:text-black transition-all duration-300"
              >
                Reservar Ahora
              </Button>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <p className="text-gray-400 mb-6">¿No encuentras lo que buscas?</p>
          <Button
            onClick={handleReservation}
            size="lg"
            className="bg-brand hover:bg-[#00B894] text-black font-bold px-8 py-4"
          >
            Consulta Personalizada
          </Button>
        </div>
      </div>
    </section>
  );
}
