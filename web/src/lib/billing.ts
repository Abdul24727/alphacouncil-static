"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, unwrap } from "@/lib/api/client";

export const PLAN_KEY = ["billing", "plan"] as const;
export const BILLING_KEY = ["billing", "summary"] as const;

/** The visitor's plan, what it allows, and whether checkout is open (api/app/plans.py).
 *  While billing is closed (early access) everyone has Pro. */
export function usePlan() {
  return useQuery({
    queryKey: PLAN_KEY,
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/billing/plan", { signal })),
    staleTime: 60_000,
  });
}

/** True only once the answer says Free: nothing is locked while the plan is loading. */
export function useIsFree() {
  return usePlan().data?.plan === "free";
}

/** The signed-in account's subscription: plan, renewal, card. */
export function useBilling(enabled = true) {
  return useQuery({
    queryKey: BILLING_KEY,
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/billing", { signal })),
    enabled,
  });
}

function useBillingMutation<T, R>(fn: (body: T) => Promise<R>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["billing"] });
      // Pro-only panels answer differently now.
      void qc.invalidateQueries({ queryKey: ["ticker"] });
    },
  });
}

export function useStartCheckout() {
  return useMutation({
    mutationFn: (body: { accept_terms: boolean; locale: "en" | "ar" }) => api.POST("/v1/billing/checkout", { body }).then(unwrap),
  });
}

export function useConfirmPayment() {
  return useBillingMutation((payment_id: string) => api.POST("/v1/billing/confirm", { body: { payment_id } }).then(unwrap));
}

export function useCancelRenewal() {
  return useBillingMutation<void, unknown>(() => api.POST("/v1/billing/cancel").then(unwrap));
}

export function useResumeRenewal() {
  return useBillingMutation<void, unknown>(() => api.POST("/v1/billing/resume").then(unwrap));
}

/** A panel's data refused because it is Pro-only (api/app/plans.py PRO_REQUIRED). */
export function isProRequired(error: unknown): boolean {
  return error instanceof ApiError && error.status === 403 && error.message === "pro_required";
}
