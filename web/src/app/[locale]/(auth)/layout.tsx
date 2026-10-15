import { Link } from "@/i18n/navigation";

/** Sign-in and sign-up: a narrow column on graphite, outside the app shell. */
export default function AuthLayout({ children }: LayoutProps<"/[locale]">) {
  return (
    <div className="flex min-h-dvh flex-col items-center px-4 py-10">
      <Link href="/home" className="mb-10 flex items-center gap-2" aria-label="AlphaCouncil">
        <span aria-hidden className="block size-3 rounded-[2px] bg-signal" />
        <span className="headline text-[19px] leading-none">AlphaCouncil</span>
      </Link>
      <main className="w-full max-w-sm">{children}</main>
    </div>
  );
}
