import Link from "next/link";
import { redirect } from "next/navigation";

import LoginForm from "@/components/auth/LoginForm";
import { setAuthCookie, getServerPrincipal } from "@/lib/auth";
import { apiFetch } from "@/lib/api-client";
import { LoginInput } from "@/lib/validators";

async function adminLoginAction(
  input: LoginInput
): Promise<{ ok: true } | { ok: false; error: string }> {
  "use server";
  const r = await apiFetch("/auth/admin/login", {
    method: "POST",
    body: JSON.stringify(input),
    authenticated: false,
  });
  if (!r.ok) {
    if (r.status === 401) return { ok: false, error: "Wrong email or password." };
    return { ok: false, error: `Server error (${r.status})` };
  }
  const body = (await r.json()) as { jwt: string };
  await setAuthCookie(body.jwt);
  return { ok: true };
}

export default async function AdminLoginPage() {
  const principal = await getServerPrincipal();
  if (principal?.role === "admin") redirect("/admin/dashboard");

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Alaba</h1>
          <p className="text-sm text-muted-foreground mt-1">Admin console</p>
        </div>
        <div className="bg-card border rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-6">Log in</h2>
          <LoginForm role="admin" action={adminLoginAction} />
          <p className="text-xs text-muted-foreground text-center mt-4">
            Producer accounts: use{" "}
            <Link href="/producer/login" className="underline">
              /producer/login
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
}
