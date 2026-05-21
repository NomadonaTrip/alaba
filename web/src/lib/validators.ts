import { z } from "zod";

export const LoginInput = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password required"),
});
export type LoginInput = z.infer<typeof LoginInput>;

export const RegisterInput = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(10, "Password must be at least 10 characters"),
  company_name: z.string().optional(),
});
export type RegisterInput = z.infer<typeof RegisterInput>;

export const ForceDeactivateInput = z.object({
  reason: z.string().min(5, "Reason is required (5+ chars)"),
});
export type ForceDeactivateInput = z.infer<typeof ForceDeactivateInput>;
