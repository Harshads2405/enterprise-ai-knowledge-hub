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

      <div className="app-sidebar-footer">
        <span className="app-sidebar-footer-label">AI Copilot</span>

        <span className="app-sidebar-footer-status">
          <span className="app-sidebar-footer-dot" aria-hidden="true" />
          System ready
        </span>
      </div>
    </aside>
  );
}