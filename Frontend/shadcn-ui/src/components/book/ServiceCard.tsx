import { Button } from '@/components/ui/button';
import { LucideIcon } from 'lucide-react';

export function ServiceCard({
  title,
  duration,
  price,
  icon: Icon,
  onSelect,
  attrsId,
}: {
  title: string;
  duration: string;
  price: string;
  icon?: LucideIcon;
  onSelect: () => void;
  attrsId?: string;
}) {
  return (
    <div
      role="listitem"
      className="rounded-2xl border border-[var(--border)] bg-[var(--card)] backdrop-blur shadow-lg shadow-black/20 transition-colors duration-150 p-5"
    >
      <div className="flex items-center gap-2 mb-2">
        {Icon ? <Icon className="h-4 w-4 text-emerald-400" /> : null}
        <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
      </div>
      <ul id={attrsId} className="text-sm text-muted-foreground space-y-1">
        <li className="before:content-['•'] before:mr-2 before:text-emerald-400">Duración: {duration}</li>
        <li className="before:content-['•'] before:mr-2 before:text-emerald-400">Precio: {price}</li>
      </ul>
      <Button
        aria-describedby={attrsId}
        onClick={onSelect}
        className="w-full mt-4 h-10 rounded-md bg-accent text-[var(--accent-contrast)] font-medium hover:bg-emerald-400 transition-colors duration-150"
      >
        Seleccionar
      </Button>
    </div>
  );
}

export default ServiceCard;
