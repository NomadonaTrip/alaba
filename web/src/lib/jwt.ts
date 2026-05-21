import { jwtVerify, type JWTPayload } from "jose";

export interface AlabaJwtClaims extends JWTPayload {
  sub: string;
  role: "viewer" | "producer" | "admin";
  kind: "access";
  user_device_id?: string;
}

const secret = new TextEncoder().encode(process.env.JWT_SECRET || "");

export async function verifyJwt(token: string): Promise<AlabaJwtClaims> {
  if (!process.env.JWT_SECRET) {
    throw new Error("JWT_SECRET env var is not set");
  }
  const { payload } = await jwtVerify(token, secret, { algorithms: ["HS256"] });
  if (payload.kind !== "access") {
    throw new Error(`Wrong kind: ${payload.kind}`);
  }
  return payload as AlabaJwtClaims;
}
