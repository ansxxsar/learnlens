import { AccountContainer } from "../components/containers/AccountContainer";
import { AuthLayout } from "../components/presentational/AuthLayout";

export function AccountPage() {
  return (
    <AuthLayout>
      <AccountContainer />
    </AuthLayout>
  );
}
