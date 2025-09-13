import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useBooking } from '@/store/booking';
import { api } from '@/lib/api';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

const mask = (s?: string) => {
  if (!s) return 'none';
  if (s.length <= 8) return s[0] + '***' + s[s.length - 1];
  return s.slice(0, 4) + '...' + s.slice(-4);
};

const Debug = () => {
  const BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8776';
  const navigate = useNavigate();
  const KEY = import.meta.env.VITE_API_KEY as string | undefined;
  const [health, setHealth] = useState<unknown>(null);
  const [ready, setReady] = useState<unknown>(null);
  const [services, setServices] = useState<unknown[]>([]);
  const [pros, setPros] = useState<unknown[]>([]);
  const [days, setDays] = useState<string[]>([]);
  const [slots, setSlots] = useState<string[]>([]);
  const [date, setDate] = useState<string>('');
  const [serviceId, setServiceId] = useState<string>('');
  const [professionalId, setProfessionalId] = useState<string>('');
  const [useGcal, setUseGcal] = useState<boolean>(false);
  const { setService, setProfessional, setDate: setStoreDate, setSlot } = useBooking((s) => s);

  useEffect(() => {
    (async () => {
      try { setHealth(await fetch(BASE + '/health').then(r => r.json())); } catch { /* noop */ }
      try { setReady(await fetch(BASE + '/ready').then(r => r.json())); } catch { /* noop */ }
      try { setServices(await api.getServices()); } catch { /* noop */ }
      try { setPros(await api.getProfessionals()); } catch { /* noop */ }
    })();
  }, [BASE]);

  const today = useMemo(() => new Date().toISOString().slice(0,10), []);

  const fetchDays = async () => {
    if (!serviceId) return;
    const start = today.slice(0,7) + '-01';
    const end = new Date(new Date(start).getFullYear(), new Date(start).getMonth()+1, 0).toISOString().slice(0,10);
    const out = await api.getDaysAvailability({ service_id: serviceId, start, end, professional_id: professionalId || undefined, use_gcal: useGcal });
    setDays(out.available_days);
  };
  const fetchSlots = async () => {
    if (!serviceId || !date) return;
    const out = await api.getSlots({ service_id: serviceId, date, professional_id: professionalId || undefined, use_gcal: useGcal });
    setSlots(out.slots);
  };
  const gotoBook = (slot: string) => {
    setService(serviceId);
    setProfessional(professionalId || null);
    setStoreDate(date);
    setSlot(slot);
    navigate('/book/confirm?service=' + encodeURIComponent(serviceId));
  };

  return (
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <Card className="border-neutral-800 bg-neutral-900 text-white">
        <CardHeader><CardTitle>Configuración de Debug</CardTitle></CardHeader>
        <CardContent className="text-sm text-neutral-300 space-y-1">
          <div>BASE: {BASE}</div>
          <div>VITE_API_KEY: {mask(KEY)}</div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        <Card className="border-neutral-800 bg-neutral-900 text-white">
          <CardHeader><CardTitle>/health & /ready</CardTitle></CardHeader>
          <CardContent>
            <div className="text-xs whitespace-pre-wrap">health: {JSON.stringify(health)}</div>
            <div className="text-xs whitespace-pre-wrap">ready: {JSON.stringify(ready)}</div>
            <div className="mt-2 space-x-2">
              <Button size="sm" onClick={async()=>setHealth(await fetch(BASE+'/health').then(r=>r.json()))}>Ping /health</Button>
              <Button size="sm" onClick={async()=>setReady(await fetch(BASE+'/ready').then(r=>r.json()))}>Ping /ready</Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-neutral-800 bg-neutral-900 text-white">
          <CardHeader><CardTitle>Catálogos</CardTitle></CardHeader>
          <CardContent>
            <div className="text-xs whitespace-pre-wrap">services: {JSON.stringify(services)}</div>
            <div className="text-xs whitespace-pre-wrap">professionals: {JSON.stringify(pros)}</div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-neutral-800 bg-neutral-900 text-white">
        <CardHeader><CardTitle>Disponibilidad</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          <div className="flex flex-wrap gap-2 items-end">
            <div>
              <div className="text-xs text-neutral-400">service_id</div>
              <input className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-sm" value={serviceId} onChange={e=>setServiceId(e.target.value)} placeholder="corte" />
            </div>
            <div>
              <div className="text-xs text-neutral-400">professional_id</div>
              <input className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-sm" value={professionalId} onChange={e=>setProfessionalId(e.target.value)} placeholder="(opcional)" />
            </div>
            <div className="flex items-center gap-2 h-[32px]">
              <Switch id="dbg-use-gcal" checked={useGcal} onCheckedChange={setUseGcal} />
              <Label htmlFor="dbg-use-gcal" className="text-xs text-neutral-300">use_gcal</Label>
            </div>
            <Button size="sm" onClick={fetchDays}>/days</Button>
          </div>
          <div className="text-xs whitespace-pre-wrap">days: {JSON.stringify(days)}</div>

          <div className="flex flex-wrap gap-2 items-end mt-4">
            <div>
              <div className="text-xs text-neutral-400">date (YYYY-MM-DD)</div>
              <input className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-sm" value={date} onChange={e=>setDate(e.target.value)} placeholder={today} />
            </div>
            <Button size="sm" onClick={fetchSlots}>/slots</Button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 mt-2">
            {slots.map(s=> (
              <Button key={s} variant="secondary" onClick={()=>gotoBook(s)}>{s.slice(11,16)}</Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Debug;
