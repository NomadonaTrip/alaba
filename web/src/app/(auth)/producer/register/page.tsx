import Link from "next/link";
import { redirect } from "next/navigation";

import RegisterForm from "@/components/auth/RegisterForm";
import { setAuthCookie, getServerPrincipal } from "@/lib/auth";
import { apiFetch } from "@/lib/api-client";
import { RegisterInput } from "@/lib/validators";

async function registerAction(
  input: RegisterInput
): Promise<{ ok: true } | { ok: false; error: string }> {
  "use server";
  const r = await apiFetch("/auth/producer/register", {
    method: "POST",
    body: JSON.stringify(input),
    authenticated: false,
  });
  if (!r.ok) {
    if (r.status === 409) return { ok: false, error: "That email is already registered." };
    if (r.status === 422) return { ok: false, error: "Password must be at least 10 characters." };
    return { ok: false, error: `Server error (${r.status})` };
  }
  const body = (await r.json()) as { jwt: string };
  await setAuthCookie(body.jwt);
  return { ok: true };
}

export default async function ProducerRegisterPage() {
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
          <h2 className="text-xl font-semibold mb-1">Create your account</h2>
          <p className="text-sm text-muted-foreground mb-6">
            Already have one?{" "}
            <Link href="/producer/login" className="underline text-foreground">
              Log in
            </Link>
          </p>
          <RegisterForm action={registerAction} />
        </div>
      </div>
    </div>
  );
}
