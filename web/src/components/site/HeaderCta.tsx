"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useMe } from "@/lib/auth";

const BUTTON =
  "rounded-panel bg-signal px-4 py-2.5 font-semibold leading-none text-signal-ink transition-colors hover:bg-text";

/**
 * The header's main button. One label for one action (design fix 9): signed out it is the
 * hero's "Start free" (sign-up); a signed-in member gets "Open the terminal" instead.
 * The server and the first paint render the signed-out button; useMe swaps it once known.
 */
export function HeaderCta() {
  const t = useTranslations("site");
  const me = useMe();
  if (me.data) {
    return (
      <Link href="/home" className={BUTTON}>
        {t("nav.open")}
      </Link>
    );
  }
  return (
    <Link href="/signup" className={BUTTON}>
      {t("hero.start")}
    </Link>
  );
}
