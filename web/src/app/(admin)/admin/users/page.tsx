import { redirect } from "next/navigation";

import { apiFetch } from "@/lib/api-client";

interface UserLookupOut {
  user_id: string;
  phone: string;
}

async function lookupAction(formData: FormData): Promise<void> {
  "use server";
  const phone = (formData.get("phone") as string | null)?.trim();
  if (!phone) return;
  const r = await apiFetch(`/admin/users/lookup?phone=${encodeURIComponent(phone)}`);
  if (!r.ok) {
    redirect(`/admin/users?error=not_found&q=${encodeURIComponent(phone)}`);
  }
  const body = (await r.json()) as UserLookupOut;
  redirect(`/admin/users/${body.user_id}/devices`);
}

export default async function AdminUsersPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; q?: string }>;
}) {
  const params = await searchParams;
  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold mb-1">Users</h1>
      <p className="text-sm text-muted-foreground mb-6">
        Look up a viewer by phone to manage their authorized devices.
      </p>
      <form action={lookupAction} className="space-y-3">
        <div>
          <label htmlFor="phone" className="block text-sm font-medium mb-1">
            Phone number
          </label>
          <input
            id="phone"
            name="phone"
            type="tel"
            placeholder="+2348031234567"
            defaultValue={params.q || ""}
            className="w-full px-3 py-2 border rounded-md text-sm"
            required
          />
        </div>
        <button
          type="submit"
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium"
        >
          Search
        </button>
        {params.error === "not_found" && (
          <p className="text-sm text-red-600">
            No user found with phone {params.q}.
          </p>
        )}
      </form>
    </div>
  );
}
