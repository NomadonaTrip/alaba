import { Badge } from "@/components/ui/badge";

import ForceDeactivateDialog from "@/components/admin/ForceDeactivateDialog";
import { formatWAT } from "@/lib/datetime";
import { ForceDeactivateInput } from "@/lib/validators";

export interface DeviceRow {
  id: string;
  display_name: string | null;
  model: string | null;
  platform: string;
  activated_at: string;
  last_seen_at: string | null;
  deactivated_at: string | null;
}

interface DeviceTableProps {
  userId: string;
  devices: DeviceRow[];
  action: (
    userId: string,
    deviceId: string,
    input: ForceDeactivateInput
  ) => Promise<{ ok: boolean; error?: string }>;
}

export default function DeviceTable({ userId, devices, action }: DeviceTableProps) {
  return (
    <table className="w-full border-collapse bg-card border rounded-lg overflow-hidden">
      <thead>
        <tr className="bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
          <th className="text-left p-3">Device</th>
          <th className="text-left p-3">Status</th>
          <th className="text-left p-3">Activated</th>
          <th className="text-left p-3">Last seen</th>
          <th className="text-right p-3"></th>
        </tr>
      </thead>
      <tbody className="text-sm">
        {devices.map((d) => {
          const isActive = d.deactivated_at === null;
          return (
            <tr key={d.id} className="border-t">
              <td className="p-3">
                <div className="font-medium">
                  {d.display_name ?? d.model ?? "Unknown device"}
                </div>
                <div className="text-xs text-muted-foreground font-mono">
                  {d.platform} · {d.id.slice(0, 8)}
                </div>
              </td>
              <td className="p-3">
                {isActive ? (
                  <Badge variant="default">Active</Badge>
                ) : (
                  <Badge variant="secondary">
                    Deactivated {d.deactivated_at && formatWAT(d.deactivated_at)}
                  </Badge>
                )}
              </td>
              <td className="p-3 text-muted-foreground">
                {formatWAT(d.activated_at)}
              </td>
              <td className="p-3 text-muted-foreground">
                {d.last_seen_at ? formatWAT(d.last_seen_at) : "—"}
              </td>
              <td className="p-3 text-right">
                {isActive ? (
                  <ForceDeactivateDialog
                    userId={userId}
                    deviceId={d.id}
                    deviceLabel={d.display_name ?? d.model ?? "this device"}
                    action={action}
                  />
                ) : (
                  <span className="text-xs text-muted-foreground">—</span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
