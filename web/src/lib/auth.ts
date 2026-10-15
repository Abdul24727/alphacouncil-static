"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, unwrap } from "@/lib/api/client";

export const ME_KEY = ["auth", "me"] as const;

/** The signed-in user, or null. */
export function useMe() {
  return useQuery({
    queryKey: ME_KEY,
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/auth/me", { signal })).user ?? null,
    staleTime: 60_000,
  });
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
  return useAuthMutation((body: { email: string; password: string; display_name?: string; locale: "en" | "ar" }) =>
    api.POST("/v1/auth/signup", { body }).then(unwrap),
  );
}

export function useSignOut() {
  return useAuthMutation<void>(() => api.POST("/v1/auth/logout").then(unwrap));
}
