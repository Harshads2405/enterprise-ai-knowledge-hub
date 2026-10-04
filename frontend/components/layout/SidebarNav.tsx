"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function SidebarNav() {
  const pathname = usePathname();

  const isChatActive = pathname === "/chat";
  const isDocumentsActive = pathname.startsWith("/documents");

  return (
    <nav className="app-sidebar-nav" aria-label="Primary navigation">
      <Link
        href="/chat"
        className={`app-sidebar-nav-item ${
          isChatActive ? "app-sidebar-nav-item-active" : ""
        }`}
        aria-current={isChatActive ? "page" : undefined}
      >
        <span>Chat</span>
      </Link>

      <Link
        href="/documents"
        className={`app-sidebar-nav-item ${
          isDocumentsActive ? "app-sidebar-nav-item-active" : ""
        }`}
        aria-current={isDocumentsActive ? "page" : undefined}
      >
        <span>Documents</span>
      </Link>
    </nav>
  );
}