import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";

export default function Page({ searchParams }: PageProps<"/[locale]/signup">) {
  return (
    <Suspense fallback={<AuthForm mode="signup" />}>
      <WithNext searchParams={searchParams} />
    </Suspense>
  );
}

async function WithNext({ searchParams }: Pick<PageProps<"/[locale]/signup">, "searchParams">) {
  const next = (await searchParams).next;
  return <AuthForm mode="signup" next={typeof next === "string" ? next : undefined} />;
}
