"use client";

import { useTranslations } from "next-intl";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { Link } from "@/i18n/navigation";
import { useMe, useResendVerification, useVerifyEmail } from "@/lib/auth";
import { tokenFromHash } from "@/lib/reset-token";

const subscribeHash = (onChange: () => void) => {
  window.addEventListener("hashchange", onChange);
  return () => window.removeEventListener("hashchange", onChange);
};

const PRIMARY = "flex h-10 items-center justify-center rounded-panel bg-signal font-semibold text-signal-ink";

/** The page an emailed "Confirm your email" link opens: it confirms as soon as it loads. */
export function VerifyEmailView() {
  const t = useTranslations("auth.verify");
  const me = useMe();
  const verify = useVerifyEmail();
  // The token is in the fragment, which only the browser has.
  const token = useSyncExternalStore(subscribeHash, () => tokenFromHash(window.location.hash), () => undefined);
  const asked = useRef<string | null>(null);
  const [state, setState] = useState<"working" | "done" | "expired">("working");

  useEffect(() => {
    if (!token || asked.current === token) return;
    asked.current = token;
    verify.mutateAsync(token).then(
      () => setState("done"),
      () => setState("expired"),
    );
  }, [token, verify]);

  if (token === null) return <Expired missing signedIn={!!me.data} />;
  if (state === "expired") return <Expired signedIn={!!me.data} />;
  if (state === "working" || token === undefined)
    return (
      <p role="status" className="text-muted">
        {t("working")}
      </p>
    );
  return (
    <div role="status" className="flex w-full flex-col gap-3" data-verified>
      <h1 className="headline text-[28px] leading-none">{t("doneTitle")}</h1>
      <p className="text-text-soft">{t("done")}</p>
      <Link href={me.data ? "/portfolio" : "/login"} className={PRIMARY}>
        {me.data ? t("continue") : t("signIn")}
      </Link>
    </div>
  );
}

function Expired({ missing = false, signedIn }: { missing?: boolean; signedIn: boolean }) {
  const t = useTranslations("auth.verify");
  const resend = useResendVerification();
  return (
    <div className="flex w-full flex-col gap-3">
      <h1 className="headline text-[28px] leading-none">{t("title")}</h1>
      <p role="alert" className="text-loss">
        {missing ? t("missing") : t("expired")}
      </p>
      {signedIn ? (
        resend.isSuccess ? (
          <p role="status" className="text-text-soft">
            {t("sent")}
          </p>
        ) : (
          <button type="button" disabled={resend.isPending} onClick={() => resend.mutate()} className={`${PRIMARY} disabled:opacity-50`}>
            {t("resend")}
          </button>
        )
      ) : (
        <Link href="/login" className={PRIMARY}>
          {t("signInForLink")}
        </Link>
      )}
    </div>
  );
}

/** Under the work area for a signed-in account that has not confirmed its address yet. */
export function VerifyEmailBanner() {
  const t = useTranslations("auth.verify");
  const me = useMe();
  const resend = useResendVerification();
  const user = me.data;
  if (!user || user.email_verified) return null;
  return (
    <div role="status" className="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b border-line bg-panel px-4 py-2 text-[13px]" data-verify-banner>
      <span className="text-text-soft">
        {t.rich("banner", { email: () => <bdi className="text-text">{user.email}</bdi> })}
      </span>
      {resend.isSuccess ? (
        <span className="text-muted">{t("sent")}</span>
      ) : (
        <button type="button" disabled={resend.isPending} onClick={() => resend.mutate()} className="text-signal hover:underline disabled:opacity-50">
          {t("resend")}
        </button>
      )}
    </div>
  );
}
