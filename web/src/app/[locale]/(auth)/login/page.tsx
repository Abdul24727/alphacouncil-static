import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";

export default function Page({ searchParams }: PageProps<"/[locale]/login">) {
  return (
    <Suspense fallback={<AuthForm mode="login" />}>
      <WithNext searchParams={searchParams} />
    </Suspense>
  );
}

async function WithNext({ searchParams }: Pick<PageProps<"/[locale]/login">, "searchParams">) {
  const next = (await searchParams).next;
  return <AuthForm mode="login" next={typeof next === "string" ? next : undefined} />;
}
