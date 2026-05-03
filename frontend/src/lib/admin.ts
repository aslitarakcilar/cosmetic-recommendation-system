export const ADMIN_EMAIL = "aslinur0506@gmail.com";

export function isAdminEmail(email?: string | null) {
  return (email ?? "").toLowerCase() === ADMIN_EMAIL;
}
