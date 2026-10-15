import { AppShell } from "@/components/shell/AppShell";

// Every signed-in page renders inside the three-pane shell.
export default function AppLayout({ children }: LayoutProps<"/[locale]">) {
  return <AppShell>{children}</AppShell>;
}
