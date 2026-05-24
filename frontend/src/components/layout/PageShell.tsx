"use client";

import { AuthGuard } from "./AuthGuard";
import { Sidebar } from "./Sidebar";

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 overflow-auto p-8">{children}</main>
      </div>
    </AuthGuard>
  );
}
