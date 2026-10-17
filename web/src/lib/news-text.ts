// What a news item shows on a page. Items are stored in one language (most in Arabic), some
// with an English headline or a summary in the other language (news_ai / the pipeline). A page
// shows, in order: the item's own headline when it is in the page's language; on English pages
// the English headline written for it; its summary in the page's language; else the original
// headline, marked as being in the other language. Nothing is translated here.

type NewsLike = {
  title: string | null;
  lang: string | null;
  title_en?: string | null;
  summary_en?: string | null;
  summary_ar?: string | null;
};

export type NewsText = {
  title: string | null;
  lang: string | undefined;
  /** A summary to show under the headline (page language only). */
  summary: string | null;
  /** The headline is a summary: clamp it like one. */
  long: boolean;
  /** Shown in the other language: "en" or "ar". */
  foreign: "en" | "ar" | null;
};

export function newsText(i: NewsLike, locale: string): NewsText {
  const page = locale === "ar" ? "ar" : "en";
  const summary = (page === "ar" ? i.summary_ar : i.summary_en) || null;
  if (i.lang === page || i.lang == null) return { title: i.title, lang: i.lang ?? undefined, summary, long: false, foreign: null };
  if (page === "en" && i.title_en) return { title: i.title_en, lang: "en", summary, long: false, foreign: null };
  if (summary) return { title: summary, lang: page, summary: null, long: true, foreign: null };
  return { title: i.title, lang: i.lang, summary: null, long: false, foreign: i.lang === "ar" ? "ar" : "en" };
}
