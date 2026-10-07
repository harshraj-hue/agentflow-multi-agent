interface StatusCardProps {
  title: string;
  ok: boolean;
  detail: string;
}

export function StatusCard({ title, ok, detail }: StatusCardProps) {
  return (
    <div className="card">
      <div className="card-title">
        <span className={`dot ${ok ? "dot-ok" : "dot-bad"}`} aria-hidden="true" />
        <h3>{title}</h3>
      </div>
      <p className="card-status">{ok ? "Operational" : "Unavailable"}</p>
      <p className="muted">{detail}</p>
    </div>
  );
}
