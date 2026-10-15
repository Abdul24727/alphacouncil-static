import {
  BackpackIcon,
  BarChartIcon,
  DashboardIcon,
  GearIcon,
  HomeIcon,
  LayersIcon,
  MixerHorizontalIcon,
} from "@radix-ui/react-icons";

export type NavKey =
  | "home"
  | "portfolio"
  | "screener"
  | "markets"
  | "templates"
  | "dashboards"
  | "settings";

export type NavItem = {
  key: NavKey;
  href: string;
  Icon: typeof HomeIcon;
};

// Sidebar order from the plan. "Home" and "My Portfolio" are separate entries
// there while the site map puts My Portfolio at /home; /portfolio is provisional.
export const MAIN_NAV: NavItem[] = [
  { key: "home", href: "/home", Icon: HomeIcon },
  { key: "portfolio", href: "/portfolio", Icon: BackpackIcon },
  { key: "screener", href: "/screener", Icon: MixerHorizontalIcon },
  { key: "markets", href: "/markets", Icon: BarChartIcon },
  { key: "templates", href: "/templates", Icon: LayersIcon },
  { key: "dashboards", href: "/dashboards", Icon: DashboardIcon },
];

export const SETTINGS_NAV: NavItem = { key: "settings", href: "/settings", Icon: GearIcon };

export function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}
