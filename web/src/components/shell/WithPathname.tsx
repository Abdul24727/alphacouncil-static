"use client";

import { Suspense } from "react";
import { usePathname } from "@/i18n/navigation";

type Render = (pathname: string | null) => React.ReactNode;

function Reader({ render }: { render: Render }) {
  return render(usePathname());
}

/**
 * Cache Components prerenders the shell without the URL, so anything that
 * reads the pathname streams in behind Suspense. The fallback is the same UI
 * with no active item (pathname = null).
 */
export function WithPathname({ render }: { render: Render }) {
  return (
    <Suspense fallback={render(null)}>
      <Reader render={render} />
    </Suspense>
  );
}
