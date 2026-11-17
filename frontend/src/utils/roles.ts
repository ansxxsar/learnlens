import type { AccountType } from "../types";

// The server picks the account type from the SDU email: a name means teacher,
// a number means student. It only labels the user; the API checks permissions.
export const accountTypeLabels: Record<AccountType, string> = {
  student: "Student",
  teacher: "Teacher",
  admin: "Admin",
};
