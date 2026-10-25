export default function StatusChip({ value }: { value: string }) {
  return <span className={`status-chip ${value}`}>{value.replace(/_/g, " ")}</span>;
}
