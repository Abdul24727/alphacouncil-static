import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { SiteLocaleSwitch } from "./SiteLocaleSwitch";
import { WRAP } from "./ui";

export function Logo({ size = "md" }: { size?: "md" | "sm" }) {
  return (
    <Link href="/" className="flex items-center gap-2.5" aria-label="AlphaCouncil">
      <span aria-hidden className={`block rounded-[2px] bg-signal ${size === "md" ? "size-3.5" : "size-3"}`} />
      <span className={`font-bold leading-none [font-stretch:112%] ${size === "md" ? "text-[20px]" : "text-[17px]"}`}>
        AlphaCouncil
      </span>
    </Link>
  );
}

export async function SiteHeader() {
  const t = await getTranslations("site.nav");
  const links = [
    [{ pathname: "/", hash: "how" }, "how"],
    [{ pathname: "/", hash: "templates" }, "templates"],
    [{ pathname: "/", hash: "markets" }, "markets"],
    ["/pricing", "pricing"],
    ["/methodology", "methodology"],
  ] as const;

  return (
    <header className={`${WRAP} flex flex-wrap items-center gap-x-7 gap-y-4 py-5`}>
      <Logo />
      <nav
        aria-label={t("primary")}
        className="order-last flex w-full flex-wrap gap-x-6 gap-y-2 text-[14.5px] text-muted lg:order-none lg:w-auto"
      >
        {links.map(([href, key]) => (
          <Link key={key} href={href} className="hover:text-text">
            {t(key)}
          </Link>
        ))}
      </nav>
      <div className="ms-auto flex items-center gap-4 text-[14.5px]">
        <SiteLocaleSwitch />
        <Link href="/login" className="hover:text-signal">
          {t("signIn")}
        </Link>
        <Link
          href="/home"
          className="rounded-panel bg-signal px-4 py-2.5 font-semibold leading-none text-signal-ink transition-colors hover:bg-text"
        >
          {t("open")}
        </Link>
      </div>
    </header>
  );
}
