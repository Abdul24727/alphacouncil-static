import { ArrowRightIcon } from "@radix-ui/react-icons";
import { Link } from "@/i18n/navigation";

/** Page width of the public site (BRAND.md landing layout), with a 16px gutter on phones. */
export const WRAP = "mx-auto w-full max-w-[1320px] px-4 sm:px-8";

/** Landing-page section title: the only place BRAND.md allows uppercase headlines. */
export const SECTION_TITLE =
  "text-[clamp(32px,4vw,52px)] font-extrabold uppercase leading-none tracking-[-0.01em] [font-stretch:85%] rtl:leading-[1.2]";

/**
 * A number read from our database (through the API). Every digit on the public pages sits
 * inside one of these; scripts/check-phase6.mjs fails the page on any digit outside them.
 */
export function Db({ children }: { children: React.ReactNode }) {
  return (
    <span data-db className="num">
      {children}
    </span>
  );
}

type LinkHref = React.ComponentProps<typeof Link>["href"];

export function ButtonLink({
  href,
  children,
  variant = "primary",
  size = "md",
}: {
  href: LinkHref;
  children: React.ReactNode;
  variant?: "primary" | "outline";
  size?: "md" | "lg";
}) {
  const pad = size === "lg" ? "px-6 py-4 text-[16px]" : "px-5 py-3.5 text-[15px]";
  const look =
    variant === "primary"
      ? "bg-signal font-semibold text-signal-ink hover:bg-text"
      : "border border-line text-text hover:border-muted";
  return (
    <Link href={href} className={`inline-flex items-center rounded-panel leading-none transition-colors ${pad} ${look}`}>
      {children}
    </Link>
  );
}

/** "Open →", mirrored in Arabic. */
export function Arrow() {
  return <ArrowRightIcon aria-hidden className="inline-block shrink-0 rtl:-scale-x-100" />;
}

/** Shown wherever the API could not answer: never a number from anywhere else. */
export function Unavailable({ children }: { children: React.ReactNode }) {
  return <span className="label-caps text-muted">{children}</span>;
}
