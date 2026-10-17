// Turn a Copilot message's parts into what the chat shows as the answer.
//
// Narration: some models write a line before calling a database tool ("Let me check the price
// history:"). Text written in a step that called a database tool is narration; it belongs in
// the collapsible steps list, not in the answer. The server applies the same rule when it
// checks citations (api/app/copilot/context.py, AnswerTrace).
//
// Citations: the server lists sentences that quote a figure without its tag, with the tag of
// the source the figure was read from (data-autocite). The tag is added at the sentence's end.

type PartLike = { type: string; text?: string; toolName?: string };

// Tools that only draw something in the chat; they never read data.
const UI_TOOLS = new Set(["suggest_follow_ups", "show_table", "show_price_chart"]);

function toolNameOf(p: PartLike): string | null {
  if (p.type === "dynamic-tool") return p.toolName ?? null;
  return p.type.startsWith("tool-") ? p.type.slice("tool-".length) : null;
}

export function splitAnswer<P extends PartLike>(parts: P[], done: boolean): { answer: string; narration: Set<P> } {
  const steps: { texts: P[]; database: boolean }[] = [{ texts: [], database: false }];
  for (const p of parts) {
    const step = steps[steps.length - 1];
    if (p.type === "step-start") steps.push({ texts: [], database: false });
    else if (p.type === "text") step.texts.push(p);
    else {
      const name = toolNameOf(p);
      if (name && !UI_TOOLS.has(name)) step.database = true;
    }
  }
  const join = (ps: P[]) => ps.map((p) => p.text ?? "").join("").trim();
  const narration = new Set(steps.filter((s) => s.database).flatMap((s) => s.texts));
  const answer = join(steps.filter((s) => !s.database).flatMap((s) => s.texts));
  // A finished message whose only text came before a lookup: show it rather than nothing.
  if (done && !answer && narration.size) return { answer: join([...narration]), narration: new Set() };
  return { answer, narration };
}

export type Autocite = { sentence: string; tags: string[] };

export function addCitations(text: string, cites: Autocite[]): string {
  let out = text;
  for (const c of cites) {
    const i = out.indexOf(c.sentence);
    if (i < 0 || !c.tags.length) continue;
    const end = i + c.sentence.length;
    const at = /[.!?؟]$/.test(c.sentence) ? end - 1 : end;
    out = out.slice(0, at) + c.tags.map((t) => ` [${t}]`).join("") + out.slice(at);
  }
  return out;
}
