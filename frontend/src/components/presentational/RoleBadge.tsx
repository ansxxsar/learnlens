import type { AccountType } from "../../types";
import { accountTypeLabels } from "../../utils/roles";

interface RoleBadgeProps {
  accountType: AccountType;
}

export function RoleBadge({ accountType }: RoleBadgeProps) {
  return (
    <span className={`role-badge role-badge--${accountType}`}>
      {accountTypeLabels[accountType]}
    </span>
  );
}
