import { z } from "zod";
import { normalizeEmail } from "./crypto";

export const emailSchema = z
  .string()
  .trim()
  .min(1, "Email is required.")
  .max(320, "Email is too long.")
  .email("Enter a valid email address.")
  .transform(normalizeEmail);

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Password is required.").max(128, "Password is too long."),
  rememberMe: z.boolean().optional().default(false),
  csrfToken: z.string().min(16, "Missing CSRF token."),
});

export const passwordResetRequestSchema = z.object({
  email: emailSchema,
});

export const passwordResetConfirmSchema = z
  .object({
    token: z.string().min(32, "Reset token is required."),
    password: z
      .string()
      .min(8, "Use at least 8 characters.")
      .max(128, "Password is too long.")
      .refine((value) => /[A-Z]/.test(value), "Add at least one uppercase letter.")
      .refine((value) => /[a-z]/.test(value), "Add at least one lowercase letter.")
      .refine((value) => /\d/.test(value), "Add at least one number.")
      .refine((value) => /[^A-Za-z0-9]/.test(value), "Add at least one symbol."),
    confirmPassword: z.string(),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

export type LoginInput = z.infer<typeof loginSchema>;
export type PasswordResetRequestInput = z.infer<typeof passwordResetRequestSchema>;
export type PasswordResetConfirmInput = z.infer<typeof passwordResetConfirmSchema>;
