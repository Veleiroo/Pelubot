import { Loader2 } from 'lucide-react';

const Loading = () => (
  <div className="flex items-center justify-center p-16" aria-label="Cargando">
    <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
  </div>
);

export default Loading;

