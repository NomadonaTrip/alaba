import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-background text-foreground">
      <div className="max-w-xl text-center space-y-6 px-6">
        <h1 className="text-4xl font-bold tracking-tight">Alaba</h1>
        <p className="text-lg text-muted-foreground">
          Nollywood films. ₦500. Download and watch offline, anytime.
        </p>
        <div className="flex gap-4 justify-center pt-4 text-sm">
          <Link
            href="/producer/login"
            className="underline text-foreground hover:opacity-70"
          >
            Producer log in
          </Link>
          <span className="text-muted-foreground">·</span>
          <Link
            href="/admin/login"
            className="underline text-muted-foreground hover:text-foreground"
          >
            Admin
          </Link>
        </div>
        <p className="text-sm text-muted-foreground pt-8">
          The Android app will be available on Google Play soon.
        </p>
      </div>
    </main>
  );
}
