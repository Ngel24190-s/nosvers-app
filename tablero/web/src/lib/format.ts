const FMT_SHORT = new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: 'short' });
const FMT_YEAR = new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
const FMT_TIME = new Intl.DateTimeFormat('es-ES', { hour: '2-digit', minute: '2-digit' });

function ymd(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function formatDateES(input: string): string {
  // Accepts YYYY-MM-DD or full ISO date-time.
  const d = new Date(input);
  if (Number.isNaN(d.getTime())) return input;
  const today = new Date();
  const todayY = ymd(today);
  const inY = ymd(d);
  if (inY === todayY) return 'hoy';
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (inY === ymd(yesterday)) return 'ayer';
  const diffDays = Math.floor((today.getTime() - d.getTime()) / 86_400_000);
  if (diffDays > 0 && diffDays < 7) return `hace ${diffDays} días`;
  if (d.getFullYear() === today.getFullYear()) return FMT_SHORT.format(d);
  return FMT_YEAR.format(d);
}

export function formatTimeES(input: string): string {
  const d = new Date(input);
  if (Number.isNaN(d.getTime())) return '';
  return FMT_TIME.format(d);
}
