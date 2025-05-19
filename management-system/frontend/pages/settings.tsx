import DashboardLayout from "./DashboardLayout";

export default function Settings() {
  return (
    <DashboardLayout>
      <h2 className="text-2xl font-semibold mb-4">Asetukset</h2>
      <div className="bg-white rounded-lg shadow p-6">
        <p>Tänne voit rakentaa järjestelmän asetussivun.</p>
      </div>
    </DashboardLayout>
  );
}
