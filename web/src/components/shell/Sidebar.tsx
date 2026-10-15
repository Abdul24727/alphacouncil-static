"use client";

import { DoubleArrowLeftIcon, EnterIcon, ExitIcon, MagnifyingGlassIcon, PersonIcon } from "@radix-ui/react-icons";
import { useLocale, useTranslations } from "next-intl";
import { Tooltip } from "radix-ui";
import { Link } from "@/i18n/navigation";
import { useMe, useSignOut } from "@/lib/auth";
import { useLayout } from "@/lib/layout-store";
import { Kbd } from "./Kbd";
import { isActive, MAIN_NAV, type NavItem, SETTINGS_NAV } from "./nav";
import { ResizeHandle } from "./ResizeHandle";
import { WithPathname } from "./WithPathname";

export function Sidebar() {
  const t = useTranslations("nav");
  const collapsed = useLayout((s) => s.sidebarCollapsed);
  const toggleSidebar = useLayout((s) => s.toggleSidebar);
  const setSearchOpen = useLayout((s) => s.setSearchOpen);

  return (
    <aside
      aria-label="Sidebar"
      className="relative flex w-[var(--sidebar-w)] shrink-0 flex-col border-e border-line bg-bg max-md:hidden sidebar-collapsed:w-12"
    >
      <div className="flex h-12 items-center gap-2 border-b border-line px-3 sidebar-collapsed:justify-center sidebar-collapsed:px-0">
        <Logo />
        <Tooltip.Root>
          <Tooltip.Trigger asChild>
            <button
              type="button"
              onClick={toggleSidebar}
              aria-label={collapsed ? t("expand") : t("collapse")}
              aria-expanded={!collapsed}
              className="ms-auto grid size-7 place-items-center rounded-panel text-muted hover:bg-panel-raised hover:text-text sidebar-collapsed:hidden"
            >
              <DoubleArrowLeftIcon className="rtl:-scale-x-100" />
            </button>
          </Tooltip.Trigger>
          <TipContent label={t("collapse")} k="B" />
        </Tooltip.Root>
      </div>

      <div className="p-2">
        <button
          type="button"
          onClick={() => setSearchOpen(true)}
          className="flex h-8 w-full items-center gap-2 rounded-panel border border-line bg-panel px-2 text-muted hover:text-text sidebar-collapsed:justify-center sidebar-collapsed:border-transparent sidebar-collapsed:bg-transparent sidebar-collapsed:px-0"
        >
          <MagnifyingGlassIcon className="shrink-0" />
          <span className="sidebar-collapsed:hidden">{t("search")}</span>
          <span className="ms-auto sidebar-collapsed:hidden">
            <Kbd k="K" />
          </span>
        </button>
      </div>

      <nav className="flex flex-col gap-0.5 px-2">
        <WithPathname
          render={(pathname) =>
            MAIN_NAV.map((item) => (
              <NavLink
                key={item.key}
                item={item}
                label={t(item.key)}
                active={pathname !== null && isActive(pathname, item.href)}
              />
            ))
          }
        />
      </nav>

      <div className="mt-auto flex flex-col gap-0.5 border-t border-line p-2">
        <WithPathname
          render={(pathname) => (
            <NavLink
              item={SETTINGS_NAV}
              label={t("settings")}
              active={pathname !== null && isActive(pathname, SETTINGS_NAV.href)}
            />
          )}
        />
        <AccountLink />
        <button
          type="button"
          onClick={toggleSidebar}
          aria-label={t("expand")}
          className="hidden h-8 place-items-center rounded-panel text-muted hover:bg-panel-raised hover:text-text sidebar-collapsed:grid"
        >
          <DoubleArrowLeftIcon className="-scale-x-100 rtl:scale-x-100" />
        </button>
        <WithPathname render={(pathname) => <LocaleSwitch pathname={pathname} />} />
      </div>

      <ResizeHandle pane="sidebar" className="end-[-3px] sidebar-collapsed:hidden" />
    </aside>
  );
}

/** Signed in: who, and sign out. Signed out: a sign-in link. */
function AccountLink() {
  const t = useTranslations("auth");
  const me = useMe();
  const signOut = useSignOut();
  const user = me.data;
  if (me.isPending) return <div className="h-8" />;
  if (!user) {
    return (
      <Link
        href="/login"
        className="flex h-8 items-center gap-2.5 rounded-panel px-2 text-muted hover:bg-panel-raised hover:text-text sidebar-collapsed:justify-center sidebar-collapsed:px-0"
      >
        <EnterIcon className="shrink-0" />
        <span className="sidebar-collapsed:hidden">{t("signIn")}</span>
      </Link>
    );
  }
  return (
    <div className="flex h-8 items-center gap-2 px-2 sidebar-collapsed:justify-center sidebar-collapsed:px-0">
      <PersonIcon className="shrink-0 text-muted" />
      <span className="min-w-0 flex-1 truncate text-text-soft sidebar-collapsed:hidden" title={t("signedInAs", { email: user.email })}>
        {user.display_name || user.email}
      </span>
      <button
        type="button"
        onClick={() => signOut.mutate()}
        aria-label={t("signOut")}
        title={t("signOut")}
        className="grid size-6 place-items-center rounded-panel text-muted hover:bg-panel-raised hover:text-text sidebar-collapsed:hidden"
      >
        <ExitIcon className="rtl:-scale-x-100" />
      </button>
    </div>
  );
}

function Logo() {
  return (
    <Link href="/home" className="flex items-center gap-2" aria-label="AlphaCouncil">
      <span aria-hidden className="block size-3 rounded-[2px] bg-signal" />
      <span className="headline text-[17px] leading-none tracking-tight sidebar-collapsed:hidden">
        AlphaCouncil
      </span>
    </Link>
  );
}

function NavLink({ item, label, active }: { item: NavItem; label: string; active: boolean }) {
  const locale = useLocale();
  const { Icon } = item;

  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <Link
          href={item.href}
          aria-current={active ? "page" : undefined}
          className={`relative flex h-8 items-center gap-2.5 rounded-panel px-2 transition-colors sidebar-collapsed:justify-center sidebar-collapsed:px-0 ${
            active
              ? "bg-panel-raised text-text before:absolute before:inset-y-1.5 before:start-0 before:w-0.5 before:rounded-full before:bg-signal"
              : "text-muted hover:bg-panel-raised hover:text-text"
          }`}
        >
          <Icon className="shrink-0" />
          <span className="truncate sidebar-collapsed:hidden">{label}</span>
        </Link>
      </Tooltip.Trigger>
      {/* Labels only need a tooltip when the sidebar is collapsed to icons. */}
      <Tooltip.Portal>
        <Tooltip.Content
          side={locale === "ar" ? "left" : "right"}
          sideOffset={8}
          className="hidden rounded-chip border border-line bg-panel-raised px-2 py-1 text-text sidebar-collapsed:block"
        >
          {label}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

function TipContent({ label, k }: { label: string; k: string }) {
  return (
    <Tooltip.Portal>
      <Tooltip.Content
        sideOffset={6}
        className="flex items-center gap-2 rounded-chip border border-line bg-panel-raised px-2 py-1 text-text"
      >
        {label}
        <Kbd k={k} />
      </Tooltip.Content>
    </Tooltip.Portal>
  );
}

function LocaleSwitch({ pathname }: { pathname: string | null }) {
  const t = useTranslations("nav");
  const locale = useLocale();

  return (
    <div
      role="group"
      aria-label={t("language")}
      className="mt-1 flex h-8 items-center gap-1 px-2 sidebar-collapsed:flex-col sidebar-collapsed:h-auto sidebar-collapsed:px-0"
    >
      {(
        [
          ["en", "EN"],
          ["ar", "ع"],
        ] as const
      ).map(([code, label], i) => (
        <span key={code} className="flex items-center gap-1">
          {i > 0 && <span className="text-line sidebar-collapsed:hidden">/</span>}
          <Link
            href={pathname ?? "/home"}
            locale={code}
            aria-current={locale === code ? "true" : undefined}
            className={`rounded-chip px-1.5 py-0.5 ${
              code === "en" ? "label-caps" : "font-sans text-[14px] leading-none"
            } ${locale === code ? "text-signal" : "text-muted hover:text-text"}`}
          >
            {label}
          </Link>
        </span>
      ))}
    </div>
  );
}
