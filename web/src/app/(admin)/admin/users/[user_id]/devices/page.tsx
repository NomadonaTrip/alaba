import Link from "next/link";

import DeviceTable, { type DeviceRow } from "@/components/admin/DeviceTable";
import { apiFetch, apiJson } from "@/lib/api-client";
import { ForceDeactivateInput } from "@/lib/validators";

interface DeviceListOut {
  devices: DeviceRow[];
  cap: number;
  active_count: number;
  deactivation_cooldown_unlock_at: string | null;
}

async function forceDeactivateAction(
  userId: string,
  deviceId: string,
  input: ForceDeactivateInput
): Promise<{ ok: boolean; error?: string }> {
  "use server";
  const r = await apiFetch(
    `/admin/users/${userId}/devices/${deviceId}/deactivate`,
    { method: "POST", body: JSON.stringify(input) }
  );
  if (!r.ok) {
    return { ok: false, error: `Server error (${r.status})` };
  }
  return { ok: true };
}

export default async function AdminUserDevicesPage({
  params,
}: {
  params: Promise<{ user_id: string }>;
}) {
  const { user_id } = await params;
  const data = await apiJson<DeviceListOut>(`/admin/users/${user_id}/devices`);

  return (
    <div>
      <div className="text-xs text-muted-foreground mb-2">
        <Link href="/admin/users" className="hover:text-foreground">
          ← Users
        </Link>
      </div>
      <h1 className="text-2xl font-bold mb-1">Devices for user {user_id.slice(0, 8)}…</h1>
      <p className="text-sm text-muted-foreground mb-6">
        {data.active_count} of {data.cap} device slots in use.
      </p>
      <DeviceTable
        userId={user_id}
        devices={data.devices}
        action={forceDeactivateAction}
      />
      <p className="text-xs text-muted-foreground mt-4">
        Force-deactivating bypasses the 90-day user cooldown. Action is logged to{" "}
        <code>admin_actions</code> with the reason you provide.
      </p>
    </div>
  );
}
