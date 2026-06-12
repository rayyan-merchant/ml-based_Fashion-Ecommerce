export default function ChartCard({ title, chart }) {
  return (
    <div className="p-4 border rounded shadow">
      <h2 className="font-bold text-lg mb-2">{title}</h2>
      <div className="h-48">
        {chart ? chart : <p>Chart placeholder</p>}
      </div>
    </div>
  );
}
