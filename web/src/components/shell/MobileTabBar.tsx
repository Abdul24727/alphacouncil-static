"use client";

import { ChatBubbleIcon, MagnifyingGlassIcon } from "@radix-ui/react-icons";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useLayout } from "@/lib/layout-store";
import { isActive, MAIN_NAV } from "./nav";
import { WithPathname } from "./WithPathname";

const TABS = MAIN_NAV.filter((item) => ["home", "portfolio", "screener"].includes(item.key));
const TAB = "flex flex-1 flex-col items-center justify-center gap-1 text-[11px]";

/** Phone: bottom tab bar replaces the sidebar; Copilot opens as a full-screen sheet. */
export function MobileTabBar() {
  const t = useTranslations("nav");
  const tc = useTranslations("copilot");
  const setSearchOpen = useLayout((s) => s.setSearchOpen);
  const setMobileCopilotOpen = useLayout((s) => s.setMobileCopilotOpen);

  return (
    <nav
      aria-label={t("tabs")}
      className="fixed inset-x-0 bottom-0 z-30 flex h-14 border-t border-line bg-bg pb-[env(safe-area-inset-bottom)] md:hidden"
    >
      <WithPathname
        render={(pathname) =>
          TABS.map(({ key, href, Icon }) => {
            const active = pathname !== null && isActive(pathname, href);
            return (
              <Link
                key={key}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`${TAB} ${active ? "text-signal" : "text-muted"}`}
              >
                <Icon />
                {t(key)}
              </Link>
            );
          })
        }
      />
      <button type="button" onClick={() => setSearchOpen(true)} className={`${TAB} text-muted`}>
        <MagnifyingGlassIcon />
        {t("search")}
      </button>
      <button type="button" onClick={() => setMobileCopilotOpen(true)} className={`${TAB} text-muted`}>
        <ChatBubbleIcon />
        {tc("title")}
      </button>
    </nav>
  );
}
