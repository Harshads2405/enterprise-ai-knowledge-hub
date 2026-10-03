import SidebarNav from "@/components/layout/SidebarNav";

export default function Sidebar() {
  return (
    <aside className="app-sidebar">
      <div className="app-sidebar-brand">
        <span className="app-sidebar-eyebrow">
          Enterprise AI Platform
        </span>

        <h1>Enterprise AI Copilot</h1>

        <p>Knowledge &amp; Operations</p>
      </div>

      <SidebarNav />
    </aside>
  );
}