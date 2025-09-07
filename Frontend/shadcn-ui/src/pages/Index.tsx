import { useNavigate } from 'react-router-dom';
import Navigation from '@/components/Navigation';
import HeroSection from '@/components/HeroSection';
import AboutSection from '@/components/AboutSection';
import ServicesSection from '@/components/ServicesSection';
import GallerySection from '@/components/GallerySection';
import ContactSection from '@/components/ContactSection';
import Footer from '@/components/Footer';

export default function Index() {
    const navigate = useNavigate();
    const handleReservation = () => navigate('/book/service');

    return (
        <div className="min-h-screen bg-black">
            <Navigation />
            <HeroSection onReservation={handleReservation} />
            <AboutSection />
            <ServicesSection />
            <GallerySection />
            <ContactSection onReservation={handleReservation} />
            <Footer />
        </div>
    );
}
