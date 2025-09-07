# Deinis Barber Club - Landing Page Development Plan

## MVP Features Implementation
- Landing page con estética minimalista, oscura y urbana
- Paleta de colores: negro/gris oscuro + acentos turquesa (#00D4AA) + blanco
- Completamente responsive

## Files to Create/Modify

### 1. index.html
- Actualizar título a "Deinis Barber Club"
- Meta tags apropiados

### 2. src/pages/Index.tsx (REWRITE)
- Hero section con imagen de fondo
- Navigation bar sticky
- Sección Sobre Nosotros
- Sección Servicios
- Galería de trabajos
- Sección Contacto
- Footer

### 3. src/components/Navigation.tsx
- Navbar responsive con logo
- Links a secciones
- Botón CTA "Reserva tu cita"

### 4. src/components/HeroSection.tsx
- Hero con imagen de fondo (herramientas de barbería)
- Título principal y subtítulo
- Botón CTA prominente

### 5. src/components/ServicesSection.tsx
- Grid de servicios con iconos
- Precios y descripciones

### 6. src/components/GallerySection.tsx
- Grid responsive de imágenes
- Lightbox effect con hover

### 7. src/components/ContactSection.tsx
- Información de contacto
- Botón WhatsApp
- Horarios

### 8. public/assets/ (COPY IMAGES)
- Copy uploaded images to public/assets/
- Rename appropriately

## Image Usage Plan
- Generated Image (herramientas): Hero background
- DSC01096.JPG (barbero trabajando): Gallery + About section
- DSC01220.JPG (cliente): Gallery section

## Color Scheme
- Primary: #000000 (negro)
- Secondary: #1a1a1a (gris oscuro)
- Accent: #00D4AA (turquesa)
- Text: #ffffff (blanco)
- Text secondary: #a0a0a0 (gris claro)