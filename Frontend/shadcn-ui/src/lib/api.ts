const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type Service = { id: string; name: string; duration_min?: number; price?: number };
export type Slot = { start: string; end: string };

async function http<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE}${path}`, {
        headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
        ...init,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json() as Promise<T>;
}

export const api = {
    getServices: () => http<Service[]>("/services"),
    getSlots: (body: { service_id: string; date: string; professional_id?: string | null }) =>
        http<Slot[]>("/slots", { method: "POST", body: JSON.stringify(body) }),
    createReservation: (payload: {
        service_id: string; date: string; time: string;
        customer_name: string; customer_phone: string;
        professional_id?: string | null;
    }) => http<{ reservation_id: string }>("/reserve", { method: "POST", body: JSON.stringify(payload) }),
};
