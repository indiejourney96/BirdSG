import ResetPasswordPage from "@/components/auth/ResetPasswordPage";

export default function ResetPasswordRoutePage({
  searchParams,
}: {
  searchParams: { token?: string };
}) {
  return <ResetPasswordPage token={searchParams.token ?? ""} />;
}
