"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Tooltip } from "radix-ui";
import { useState } from "react";
import { ApiError } from "@/lib/api/client";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        // One retry for network and server errors; a 4xx (Pro only, not found) will not change.
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: (count, error) => count < 1 && !(error instanceof ApiError && error.status >= 400 && error.status < 500),
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <Tooltip.Provider delayDuration={300}>{children}</Tooltip.Provider>
    </QueryClientProvider>
  );
}
