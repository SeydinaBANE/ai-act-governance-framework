import { Sidebar } from "@/components/layout/Sidebar";
import { AuthGuard } from "@/components/layout/AuthGuard";
import { DashboardContent } from "./DashboardContent";

export default function DashboardPage() {
  return (
    <AuthGuard>
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 overflow-auto p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              Tableau de bord
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Vue d&apos;ensemble de la conformité AI Act de votre portfolio
            </p>
          </div>
          <DashboardContent />
        </main>
      </div>
    </AuthGuard>
  );
}
