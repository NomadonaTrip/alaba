import { cookies } from "next/headers";
import { verifyJwt, type AlabaJwtClaims } from "@/lib/jwt";

const COOKIE_NAME = "auth_token";
const TWENTY_FOUR_HOURS = 60 * 60 * 24;

export async function setAuthCookie(jwt: string): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(COOKIE_NAME, jwt, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: TWENTY_FOUR_HOURS,
  });
}

export async function clearAuthCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(COOKIE_NAME);
}

export async function getServerPrincipal(): Promise<AlabaJwtClaims | null> {
  const cookieStore = await cookies();
  const jwt = cookieStore.get(COOKIE_NAME)?.value;
  if (!jwt) return null;
  try {
    return await verifyJwt(jwt);
  } catch {
    return null;
  }
}
