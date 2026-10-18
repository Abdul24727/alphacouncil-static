"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSyncExternalStore } from "react";
import { api, unwrap } from "@/lib/api/client";

export const ME_KEY = ["auth", "me"] as const;

const subscribeNever = () => () => {};

/** The signed-in user, or null. */
export function useMe() {
  const hydrated = useSyncExternalStore(subscribeNever, () => true, () => false);
  const q = useQuery({
    queryKey: ME_KEY,
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/auth/me", { signal })).user ?? null,
    staleTime: 60_000,
  });
  // The server always renders "pending". Another part of the page (the shell) may already have
  // the answer when this component hydrates; showing it then would not match the server HTML.
  return hydrated ? q : ({ ...q, data: undefined, isPending: true } as typeof q);
}

/** After sign-in/out, everything user-specific is refetched. */
function useAuthMutation<T>(fn: (body: T) => Promise<unknown>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ME_KEY });
      void qc.invalidateQueries({ queryKey: ["portfolio"] });
      void qc.invalidateQueries({ queryKey: ["prefs"] });
    },
  });
}

export function useSignIn() {
  return useAuthMutation((body: { email: string; password: string }) =>
    api.POST("/v1/auth/login", { body }).then(unwrap),
  );
}

export function useSignUp() {
  return useAuthMutation(
    (body: { email: string; password: string; display_name?: string; locale: "en" | "ar"; accept_terms: boolean }) =>
      api.POST("/v1/auth/signup", { body }).then(unwrap),
  );
}

/** Deletes the account and everything stored with it; asks for the password again. */
export function useDeleteAccount() {
  return useAuthMutation((body: { password: string }) => api.POST("/v1/me/delete", { body }).then(unwrap));
}

export function useSignOut() {
  return useAuthMutation<void>(() => api.POST("/v1/auth/logout").then(unwrap));
}

/** Asks for a "Forgot password?" email. The API answers the same whether or not an account
 *  has the address, so this only ever says "sent if it exists". */
export function useForgotPassword() {
  return useMutation({
    mutationFn: (body: { email: string; locale: "en" | "ar" }) =>
      api.POST("/v1/auth/forgot-password", { body }).then(unwrap),
  });
}

/** Sets a new password with the emailed link's token. The account's other sessions end and
 *  this browser is signed in. */
export function useResetPassword() {
  return useAuthMutation((body: { token: string; password: string; accept_terms: boolean }) =>
    api.POST("/v1/auth/reset-password", { body }).then(unwrap),
  );
}

/** Whether the link's account must accept the Terms and Privacy Policy as it saves the new
 *  password (an account brought over from the old site without an acceptance). Uses nothing up;
 *  a used or expired link is still reported by the save. */
export function useResetLink(token: string | null | undefined) {
  return useQuery({
    queryKey: ["auth", "reset-link", token],
    queryFn: async () => unwrap(await api.POST("/v1/auth/reset-password/check", { body: { token: token! } })),
    enabled: !!token,
    staleTime: Infinity,
    retry: false,
  });
}
