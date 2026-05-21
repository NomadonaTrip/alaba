import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";

export const config = {
  matcher: ["/producer/((?!login|register).*)", "/admin/((?!login).*)"],
};

const JWT_SECRET = process.env.JWT_SECRET || "";

export async function proxy(req: NextRequest) {
  const isProducerRoute = req.nextUrl.pathname.startsWith("/producer");
  const loginUrl = isProducerRoute ? "/producer/login" : "/admin/login";
  const token = req.cookies.get("auth_token")?.value;

  if (!token) {
    return NextResponse.redirect(new URL(loginUrl, req.url));
  }

  try {
    const secret = new TextEncoder().encode(JWT_SECRET);
    const { payload } = await jwtVerify(token, secret, { algorithms: ["HS256"] });
    const role = (payload as { role?: string }).role;
    if (isProducerRoute && role !== "producer") {
      return NextResponse.redirect(new URL("/producer/login", req.url));
    }
    if (req.nextUrl.pathname.startsWith("/admin") && role !== "admin") {
      return NextResponse.redirect(new URL("/admin/login", req.url));
    }
    return NextResponse.next();
  } catch {
    const res = NextResponse.redirect(new URL(loginUrl, req.url));
    res.cookies.delete("auth_token");
    return res;
  }
}
