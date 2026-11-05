import data from "@/content/data-labels.json";

import { makeDataLabel } from "./data-labels-core";

// Statement lines, event names and capital-change types are stored in one language
// (Arabic for most tickers, English for some). Show each in the page's language when
// the dictionary knows it; otherwise as stored, tagged with its own language. Pass the
// statement for a statement line: a few lines mean something else inside one statement
// (data-labels.json, `in_statement`; the lookup is lib/data-labels-core.ts).
export const dataLabel = makeDataLabel(data);
