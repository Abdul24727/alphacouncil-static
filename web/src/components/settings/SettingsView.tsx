"use client";

import { useLocale, useTranslations } from "next-intl";
import { Panel } from "@/components/panel/Panel";
import { Link, usePathname, useRouter } from "@/i18n/navigation";
import { useMe, useSignOut } from "@/lib/auth";
import { type Decimals, type FontSize, useSettings } from "@/lib/settings-store";

function Choice<T extends string | number>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string; lang?: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5 border-t border-line py-3 first:border-t-0 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-text">{label}</span>
      <div role="radiogroup" aria-label={label} className="flex rounded-chip border border-line p-0.5">
        {options.map((o) => (
          <button
            key={String(o.value)}
            type="button"
            role="radio"
            aria-checked={value === o.value}
            onClick={() => onChange(o.value)}
            lang={o.lang}
            className={`rounded-[3px] px-3 py-1 ${value === o.value ? "bg-panel-raised text-text" : "text-muted hover:text-text"}`}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function SettingsView() {
  const t = useTranslations("settings");
  const ta = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const { decimals, fontSize, controlsOnHover, set } = useSettings();
  const me = useMe();
  const signOut = useSignOut();

  return (
    <div className="@container min-h-0 flex-1 overflow-y-auto">
      <div className="grid grid-cols-12 gap-2.5 p-2.5">
        <Panel id="settings.display" title={t("display")} className="col-span-12 @4xl:col-span-7">
          <Choice
            label={t("language")}
            value={locale}
            options={[
              // Each language is named in itself.
              { value: "en", label: "English", lang: "en" },
              { value: "ar", label: "العربية", lang: "ar" },
            ]}
            onChange={(v) => router.replace(pathname, { locale: v })}
          />
          <Choice<Decimals>
            label={t("decimals")}
            value={decimals}
            options={[
              { value: "auto", label: t("decimalsAuto") },
              { value: 2, label: "0.00" },
              { value: 3, label: "0.000" },
            ]}
            onChange={(v) => set({ decimals: v })}
          />
          <Choice<FontSize>
            label={t("fontSize")}
            value={fontSize}
            options={[
              { value: "sm", label: t("small") },
              { value: "md", label: t("medium") },
              { value: "lg", label: t("large") },
            ]}
            onChange={(v) => set({ fontSize: v })}
          />
          <Choice<"always" | "hover">
            label={t("controls")}
            value={controlsOnHover ? "hover" : "always"}
            options={[
              { value: "always", label: t("controlsAlways") },
              { value: "hover", label: t("controlsHover") },
            ]}
            onChange={(v) => set({ controlsOnHover: v === "hover" })}
          />
          <p className="pt-2 text-[12px] text-muted">{me.data ? t("savedToAccount") : t("savedToBrowser")}</p>
        </Panel>

        <Panel id="settings.account" title={t("account")} className="col-span-12 @4xl:col-span-5">
          {me.data ? (
            <div className="flex flex-col items-start gap-3">
              <p className="text-text-soft">{ta("signedInAs", { email: me.data.email })}</p>
              <button type="button" onClick={() => signOut.mutate()} className="rounded-panel border border-line px-3 py-1.5 text-text hover:bg-panel-raised">
                {ta("signOut")}
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-start gap-3">
              <p className="text-text-soft">{ta("required")}</p>
              <div className="flex gap-2">
                <Link href="/signup?next=/settings" className="rounded-panel bg-signal px-3 py-1.5 font-semibold text-signal-ink">
                  {ta("signupLink")}
                </Link>
                <Link href="/login?next=/settings" className="rounded-panel border border-line px-3 py-1.5 text-text hover:bg-panel-raised">
                  {ta("signIn")}
                </Link>
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
