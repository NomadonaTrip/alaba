import Link from "next/link";
import { redirect } from "next/navigation";

import LoginForm from "@/components/auth/LoginForm";
import { setAuthCookie, getServerPrincipal } from "@/lib/auth";
import { apiFetch } from "@/lib/api-client";
import { LoginInput } from "@/lib/validators";

async function loginAction(
  input: LoginInput
): Promise<{ ok: true } | { ok: false; error: string }> {
  "use server";
  const r = await apiFetch("/auth/producer/login", {
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

export default async function ProducerLoginPage() {
  const principal = await getServerPrincipal();
  if (principal?.role === "producer") redirect("/producer/dashboard");

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Alaba</h1>
          <p className="text-sm text-muted-foreground mt-1">For producers</p>
        </div>
        <div className="bg-card border rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-1">Welcome back</h2>
          <p className="text-sm text-muted-foreground mb-6">
            New here?{" "}
            <Link href="/producer/register" className="underline text-foreground">
              Register
            </Link>
          </p>
          <LoginForm role="producer" action={loginAction} />
        </div>
      </div>
    </div>
  );
}
