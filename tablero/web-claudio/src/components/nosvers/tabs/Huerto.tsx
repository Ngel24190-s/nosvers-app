export default function Huerto() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl">Huerto</h2>
      <p className="text-muted text-sm">
        Datos del huerto se publicarán cuando el worker `nosvers_huerto`
        esté activo. Mientras tanto, dicta notas con el PTT y caerán en
        <code className="bg-border/30 px-1 mx-1">nosvers/huerto/</code>.
      </p>
    </div>
  );
}
