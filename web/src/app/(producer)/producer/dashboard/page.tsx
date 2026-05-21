import { apiJson } from "@/lib/api-client";

interface MeProducerOut {
  role: "producer";
  producer_id: string;
  email: string;
  company_name: string | null;
  verified: boolean;
  agreement_accepted_at: string | null;
}

export default async function ProducerDashboard() {
  const me = await apiJson<MeProducerOut>("/me");

  let banner: { color: string; icon: string; title: string; body: string } | null = null;
  if (!me.verified) {
    banner = {
      color: "yellow",
      icon: "⏳",
      title: "Your account is awaiting verification",
      body: "An admin needs to verify your identity before you can accept the Distribution Agreement and upload films. You'll see a notification here when it's done.",
    };
  } else if (!me.agreement_accepted_at) {
    banner = {
      color: "blue",
      icon: "📄",
      title: "Distribution Agreement coming soon",
      body: "You've been verified. Agreement signing arrives in Wave 2.",
    };
  } else {
    banner = {
      color: "green",
      icon: "✓",
      title: "Account ready",
      body: "Upload, films, and payouts open up in upcoming releases.",
    };
  }

  const colorClasses: Record<string, { bg: string; border: string; titleC: string; bodyC: string }> = {
    yellow: { bg: "bg-yellow-50", border: "border-yellow-300", titleC: "text-yellow-900", bodyC: "text-yellow-800" },
    blue: { bg: "bg-blue-50", border: "border-blue-300", titleC: "text-blue-900", bodyC: "text-blue-800" },
    green: { bg: "bg-green-50", border: "border-green-300", titleC: "text-green-900", bodyC: "text-green-800" },
  };
  const c = colorClasses[banner.color];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
      <p className="text-sm text-muted-foreground mb-6">
        Welcome{me.company_name ? `, ${me.company_name}` : ""}.
      </p>

      <div
        className={`rounded-lg p-4 mb-8 border ${c.bg} ${c.border}`}
        role="status"
      >
        <div className="flex gap-3">
          <div className="text-2xl">{banner.icon}</div>
          <div>
            <div className={`font-semibold mb-1 ${c.titleC}`}>{banner.title}</div>
            <p className={`text-sm ${c.bodyC}`}>{banner.body}</p>
          </div>
        </div>
      </div>

      <div className="border border-dashed rounded-lg p-12 text-center text-muted-foreground">
        <p className="text-sm mb-1">Films, licenses, revenue, geo breakdown</p>
        <p className="text-xs">Full dashboard arrives in Wave 8.</p>
      </div>
    </div>
  );
}
