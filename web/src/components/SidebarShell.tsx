import Link from "next/link";

export interface NavItem {
  label: string;
  href: string;
  enabled: boolean;
  wave: string | null;
}

interface SidebarShellProps {
  email: string;
  title: string;
  navItems: NavItem[];
}

export default function SidebarShell({ email, title, navItems }: SidebarShellProps) {
  return (
    <aside className="w-56 border-r bg-card p-4 flex flex-col h-screen sticky top-0">
      <div className="text-lg font-bold mb-1">{title}</div>
      <div className="text-xs text-muted-foreground mb-6 truncate">{email}</div>
      <nav className="space-y-1 flex-1">
        {navItems.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className={`block px-2 py-1.5 rounded text-sm ${
              item.enabled
                ? "bg-muted/50 font-medium"
                : "text-muted-foreground pointer-events-none"
            }`}
          >
            {item.label}
            {item.wave && (
              <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                {item.wave}
              </span>
            )}
          </Link>
        ))}
      </nav>
      <form action="/api/auth/logout" method="POST">
        <button
          type="submit"
          className="w-full text-left text-xs text-muted-foreground py-2 hover:text-foreground"
        >
          Log out
        </button>
      </form>
    </aside>
  );
}
