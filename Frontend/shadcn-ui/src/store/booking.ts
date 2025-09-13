import { create } from 'zustand';

type BookingState = {
  serviceId?: string;
  serviceName?: string; // Nombre descriptivo del servicio.
  professionalId?: string | null;
  date?: string; // YYYY-MM-DD
  slotStart?: string; // ISO string
  setService: (serviceId: string, serviceName?: string) => void;
  setProfessional: (proId: string | null) => void;
  setDate: (date: string) => void;
  setSlot: (isoStart: string) => void;
  reset: () => void;
};

export const useBooking = create<BookingState>((set) => ({
  serviceId: undefined,
  serviceName: undefined,
  professionalId: null,
  date: undefined,
  slotStart: undefined,
  setService: (serviceId, serviceName) =>
    set({ serviceId, serviceName, professionalId: null, date: undefined, slotStart: undefined }),
  setProfessional: (professionalId) => set({ professionalId }),
  setDate: (date) => set({ date, slotStart: undefined }),
  setSlot: (isoStart) => set({ slotStart: isoStart }),
  reset: () =>
    set({ serviceId: undefined, serviceName: undefined, professionalId: null, date: undefined, slotStart: undefined }),
}));

