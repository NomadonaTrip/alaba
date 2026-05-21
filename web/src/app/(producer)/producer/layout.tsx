import { redirect } from "next/navigation";

import Sidebar from "@/components/producer/Sidebar";
import { getServerPrincipal } from "@/lib/auth";
import { apiJson } from "@/lib/api-client";

interface MeProducerOut {
  role: "producer";
  producer_id: string;
  email: string;
  company_name: string | null;
  verified: boolean;
  agreement_accepted_at: string | null;
}

export default async function ProducerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const principal = await getServerPrincipal();
  if (!principal || principal.role !== "producer") redirect("/producer/login");

  // Fetch /me for the email display in sidebar
  let email = "";
  try {
    const me = await apiJson<MeProducerOut>("/me");
    email = me.email;
  } catch {
    redirect("/producer/login");
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <Sidebar email={email} />
      <main className="flex-1 p-8 max-w-5xl">{children}</main>
    </div>
  );
}
