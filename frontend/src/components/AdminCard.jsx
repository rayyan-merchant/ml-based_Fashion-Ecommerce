export default function AdminCard({ title, value, children }) {
  return (
    <div className="p-4 border rounded shadow">
      <h2 className="font-bold text-lg mb-2">{title}</h2>
      <p className="text-2xl mb-2">{value}</p>
      <div>{children}</div>
    </div>
  );
}
