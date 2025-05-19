import DashboardLayout from "./DashboardLayout";

export default function Dashboard() {
  return (
    <DashboardLayout>
      <h2 className="text-2xl font-semibold mb-4">Tervetuloa hallintapaneeliin!</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-bold mb-2">Käyttäjät</h3>
          <p>Hallinnoi käyttäjiä ja oikeuksia.</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-bold mb-2">Asetukset</h3>
          <p>Muokkaa järjestelmän asetuksia.</p>
        </div>
      </div>
    </DashboardLayout>
  );
}
