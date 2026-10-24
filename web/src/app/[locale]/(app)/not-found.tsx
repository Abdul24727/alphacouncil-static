import { EmptyRoom } from "@/components/shell/EmptyRoom";

/**
 * Anything under the app shell that does not exist — most often a stock symbol that is mistyped or
 * a listing that stopped trading (api/app/data/not_listed.json). The room is drawn with no question
 * before it; not-found.tsx takes no params, so the copy never names the symbol.
 */
export default function NotFound() {
  return <EmptyRoom />;
}
