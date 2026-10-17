// Run with: npm test
import assert from "node:assert/strict";
import { test } from "node:test";
import { addCitations, splitAnswer } from "./copilot-answer.ts";

const parts = [
  { type: "step-start" },
  { type: "text", text: "Let me check the price history:" },
  { type: "tool-get_price_history" },
  { type: "step-start" },
  { type: "text", text: "The last close was 230.00 AED [P1]." },
  { type: "tool-suggest_follow_ups" },
];

test("copilot: text written in a step that read the database is narration, not the answer", () => {
  const { answer, narration } = splitAnswer(parts, true);
  assert.equal(answer, "The last close was 230.00 AED [P1].");
  assert.deepEqual([...narration].map((p) => p.text), ["Let me check the price history:"]);
});

test("copilot: a finished answer that only has narration still shows its text", () => {
  const { answer, narration } = splitAnswer(parts.slice(0, 3), true);
  assert.equal(answer, "Let me check the price history:");
  assert.equal(narration.size, 0);
  assert.equal(splitAnswer(parts.slice(0, 3), false).answer, "");
});

test("copilot: missing tags are added at the end of their sentence", () => {
  const text = "Book value per share is −4.81 and EPS is -2.52. The yield is not available.";
  const cites = [{ sentence: "Book value per share is −4.81 and EPS is -2.52.", tags: ["P1", "DB"] }];
  assert.equal(addCitations(text, cites), "Book value per share is −4.81 and EPS is -2.52 [P1] [DB]. The yield is not available.");
  assert.equal(addCitations(text, [{ sentence: "Not in the text.", tags: ["P1"] }]), text);
});
