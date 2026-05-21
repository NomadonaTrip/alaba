import SidebarShell, { type NavItem } from "@/components/SidebarShell";

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/producer/dashboard", enabled: true, wave: null },
  { label: "Films", href: "#", enabled: false, wave: "Wave 3" },
  { label: "Upload", href: "#", enabled: false, wave: "Wave 3" },
  { label: "Payouts", href: "#", enabled: false, wave: "Wave 8" },
  { label: "Settings", href: "#", enabled: false, wave: "Wave 9" },
];

export default function Sidebar({ email }: { email: string }) {
  return <SidebarShell title="Alaba" email={email} navItems={NAV_ITEMS} />;
}
