import Link from "next/link";

export default function SidebarNav() {
  return (
    <nav className="app-sidebar-nav" aria-label="Primary navigation">
      <Link href="/chat" className="app-sidebar-nav-item">
        <span>Chat</span>
      </Link>

      <Link href="/documents" className="app-sidebar-nav-item">
        <span>Documents</span>
      </Link>
    </nav>
  );
}