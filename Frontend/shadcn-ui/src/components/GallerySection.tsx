import { useState } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';

export default function GallerySection() {
  const [selectedImage, setSelectedImage] = useState<number | null>(null);

  const galleryImages = [
    {
      src: "/assets/barber-working.jpg",
      alt: "Deinis trabajando con precisión",
      category: "Trabajo Profesional"
    },
    {
      src: "/assets/client-service.jpg",
      alt: "Atención personalizada al cliente",
      category: "Experiencia Cliente"
    },
    {
      src: "/assets/barber-tools.jpg",
      alt: "Herramientas profesionales de barbería",
      category: "Equipamiento"
    },
    // Imágenes adicionales de ejemplo (placeholder)
    {
      src: "/assets/barber-working.jpg",
      alt: "Corte de precisión",
      category: "Cortes"
    },
    {
      src: "/assets/client-service.jpg",
      alt: "Resultado final",
      category: "Antes y Después"
    },
    {
      src: "/assets/barber-tools.jpg",
      alt: "Ambiente del local",
      category: "Instalaciones"
    }
  ];

  const openLightbox = (index: number) => {
    setSelectedImage(index);
  };

  const closeLightbox = () => {
    setSelectedImage(null);
  };

  const nextImage = () => {
    if (selectedImage !== null) {
      setSelectedImage((selectedImage + 1) % galleryImages.length);
    }
  };

  const prevImage = () => {
    if (selectedImage !== null) {
      setSelectedImage(selectedImage === 0 ? galleryImages.length - 1 : selectedImage - 1);
    }
  };

  const handleReservation = () => {
    window.open('https://wa.me/1234567890?text=Hola, me gustaría reservar una cita en Deinis Barber Club', '_blank');
  };

  return (
    <section id="galeria" className="py-20 bg-[#1a1a1a]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Galería de <span className="text-[#00D4AA]">Trabajos</span>
          </h2>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            Descubre nuestro trabajo y la experiencia que ofrecemos. 
            Cada corte es una obra de arte, cada cliente una historia única.
          </p>
        </div>

        {/* Gallery Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {galleryImages.map((image, index) => (
            <div
              key={index}
              className="relative group cursor-pointer overflow-hidden rounded-lg bg-black"
              onClick={() => openLightbox(index)}
            >
              <img
                src={image.src}
                alt={image.alt}
                className="w-full h-80 object-cover transition-transform duration-500 group-hover:scale-110"
              />
              
              {/* Overlay */}
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-[#00D4AA] text-sm font-semibold mb-2">
                    {image.category}
                  </div>
                  <div className="text-white text-lg font-bold">
                    Ver Imagen
                  </div>
                </div>
              </div>

              {/* Category Badge */}
              <div className="absolute top-4 left-4 bg-[#00D4AA] text-black px-3 py-1 rounded-full text-sm font-semibold">
                {image.category}
              </div>
            </div>
          ))}
        </div>

        {/* Lightbox */}
        {selectedImage !== null && (
          <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
            <div className="relative max-w-4xl max-h-full">
              <img
                src={galleryImages[selectedImage].src}
                alt={galleryImages[selectedImage].alt}
                className="max-w-full max-h-full object-contain"
              />
              
              {/* Close Button */}
              <button
                onClick={closeLightbox}
                className="absolute top-4 right-4 text-white hover:text-[#00D4AA] transition-colors"
              >
                <X size={32} />
              </button>

              {/* Navigation Buttons */}
              <button
                onClick={prevImage}
                className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white hover:text-[#00D4AA] transition-colors"
              >
                <ChevronLeft size={48} />
              </button>
              <button
                onClick={nextImage}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white hover:text-[#00D4AA] transition-colors"
              >
                <ChevronRight size={48} />
              </button>

              {/* Image Info */}
              <div className="absolute bottom-4 left-4 text-white">
                <div className="text-[#00D4AA] text-sm font-semibold">
                  {galleryImages[selectedImage].category}
                </div>
                <div className="text-lg">
                  {galleryImages[selectedImage].alt}
                </div>
              </div>

              {/* Image Counter */}
              <div className="absolute bottom-4 right-4 text-white bg-black/50 px-3 py-1 rounded-full">
                {selectedImage + 1} / {galleryImages.length}
              </div>
            </div>
          </div>
        )}

        {/* Call to Action */}
        <div className="text-center mt-12">
          <p className="text-gray-400 mb-6">¿Te gusta lo que ves?</p>
          <button
            onClick={handleReservation}
            className="bg-[#00D4AA] hover:bg-[#00B894] text-black font-bold px-8 py-4 rounded-lg transition-all duration-300 transform hover:scale-105"
          >
            RESERVA TU CITA AHORA
          </button>
        </div>
      </div>
    </section>
  );
}