import { redirect } from "next/navigation";

import AdminSidebar from "@/components/admin/Sidebar";
import { getServerPrincipal } from "@/lib/auth";
import { apiJson } from "@/lib/api-client";

interface MeAdminOut {
  role: "admin";
  admin_id: string;
  email: string;
}

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const principal = await getServerPrincipal();
  if (!principal || principal.role !== "admin") redirect("/admin/login");

  let email = "";
  try {
    const me = await apiJson<MeAdminOut>("/me");
    email = me.email;
  } catch {
    redirect("/admin/login");
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <AdminSidebar email={email} />
      <main className="flex-1 p-8 max-w-5xl">{children}</main>
    </div>
  );
}
