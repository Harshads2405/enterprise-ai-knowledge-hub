import type { ReactNode } from "react";

import Sidebar from "@/components/layout/Sidebar";

type AppShellProps = {
  children: ReactNode;
};

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <Sidebar />

      <main className="app-shell-content">
        {children}
      </main>
    </div>
  );
}