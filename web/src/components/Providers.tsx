"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Tooltip } from "radix-ui";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <Tooltip.Provider delayDuration={300}>{children}</Tooltip.Provider>
    </QueryClientProvider>
  );
}
