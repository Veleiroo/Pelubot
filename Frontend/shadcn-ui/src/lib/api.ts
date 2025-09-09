const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8776";
const API_KEY: string | undefined = import.meta.env.VITE_API_KEY;
const DEBUG = /^(1|true|yes|y)$/i.test(String(import.meta.env.VITE_ENABLE_DEBUG ?? "0"));

export type Service = { id: string; name: string; duration_min: number; price_eur: number };
export type Professional = { id: string; name: string; services?: string[] };

type SlotsOut = { service_id: string; date: string; professional_id?: string | null; slots: string[] };
type ActionResult = { ok: boolean; message: string };
type DaysAvailabilityOut = { service_id: string; start: string; end: string; professional_id?: string | null; available_days: string[] };

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json", ...(init?.headers as any) };
  if (API_KEY) headers["X-API-Key"] = API_KEY;
  const url = `${BASE}${path}`;
  const started = performance.now();
  DEBUG && console.debug("HTTP", init?.method || "GET", url, init?.body ? JSON.parse(String(init.body)) : undefined);
  const res = await fetch(url, {
    headers,
    ...init,
  });
  const ms = Math.round(performance.now() - started);
  let text: string | undefined;
  if (!res.ok) {
    try { text = await res.text(); } catch {}
    DEBUG && console.warn("HTTP ERR", res.status, url, `${ms}ms`, text);
    throw new Error(`HTTP ${res.status}`);
  }
  try {
    const data = await res.json() as T;
    DEBUG && console.debug("HTTP OK", res.status, url, `${ms}ms`, data);
    return data;
  } catch (e) {
    DEBUG && console.warn("HTTP JSON ERR", url, `${ms}ms`);
    throw e;
  }
}

export const api = {
  // Catalogos
  getServices: () => http<Service[]>("/services"),
  getProfessionals: () => http<Professional[]>("/professionals"),

  // Slots: el backend espera { service_id, date_str, professional_id? }
  getSlots: (args: { service_id: string; date: string; professional_id?: string | null; use_gcal?: boolean }) =>
    http<SlotsOut>("/slots", {
      method: "POST",
      body: JSON.stringify({
        service_id: args.service_id,
        date_str: args.date,
        professional_id: args.professional_id ?? undefined,
        use_gcal: args.use_gcal ?? undefined,
      }),
    }),

  // Crear reserva: el backend espera { service_id, professional_id, start }
  createReservation: (payload: { service_id: string; professional_id: string; start: string }) =>
    http<ActionResult>("/reservations", { method: "POST", body: JSON.stringify(payload) }),

  // Disponibilidad por días para un rango [start, end]
  getDaysAvailability: (args: { service_id: string; start: string; end: string; professional_id?: string | null; use_gcal?: boolean }) =>
    http<DaysAvailabilityOut>("/slots/days", {
      method: "POST",
      body: JSON.stringify({
        service_id: args.service_id,
        start: args.start,
        end: args.end,
        professional_id: args.professional_id ?? undefined,
        use_gcal: args.use_gcal ?? undefined,
      }),
    }),
};
