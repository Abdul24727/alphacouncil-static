import { create } from "zustand";

/**
 * Ticker groups: every panel in a group shows the same ticker. Changing it in
 * one panel (or clicking a peer row) changes it for the whole group.
 * BRAND.md fixes group 1 to `signal`; colours for further groups are still open.
 */
export type GroupId = 1;

export const GROUP_COLOR: Record<GroupId, string> = {
  1: "bg-signal",
};

type GroupState = {
  tickers: Partial<Record<GroupId, string>>;
  setGroupTicker: (group: GroupId, slug: string) => void;
};

export const useTickerGroups = create<GroupState>()((set) => ({
  tickers: {},
  setGroupTicker: (group, slug) =>
    set((s) => (s.tickers[group] === slug ? s : { tickers: { ...s.tickers, [group]: slug } })),
}));

export const useGroupTicker = (group: GroupId) => useTickerGroups((s) => s.tickers[group]);
