import SidebarShell, { type NavItem } from "@/components/SidebarShell";

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/admin/dashboard", enabled: true, wave: null },
  { label: "Review", href: "#", enabled: false, wave: "Wave 3" },
  { label: "Producers", href: "#", enabled: false, wave: "Wave 2" },
  { label: "Users", href: "/admin/users", enabled: true, wave: null },
];

export default function AdminSidebar({ email }: { email: string }) {
  return <SidebarShell title="Alaba Admin" email={email} navItems={NAV_ITEMS} />;
}
