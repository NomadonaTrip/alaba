import { NextResponse } from "next/server";

export async function POST() {
  const res = NextResponse.redirect(
    new URL("/", process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3000"),
    { status: 303 }
  );
  res.cookies.delete("auth_token");
  return res;
}
