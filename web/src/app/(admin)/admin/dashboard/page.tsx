export default function AdminDashboard() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
      <p className="text-sm text-muted-foreground mb-6">
        Welcome to the admin console.
      </p>
      <div className="border border-dashed rounded-lg p-12 text-center text-muted-foreground">
        <p className="text-sm mb-1">Platform metrics, top films, top producers</p>
        <p className="text-xs">Full dashboard arrives in Wave 8.</p>
      </div>
    </div>
  );
}
