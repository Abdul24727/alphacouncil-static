// Run with: npm test   (Node's built-in runner; Node 24 strips the types)
import assert from "node:assert/strict";
import { test } from "node:test";
import { tokenFromHash } from "./reset-token.ts";

test("reset links: the token comes from the fragment", () => {
  const token = "Zk3n0_q-8vXwYp2LmT6rB1cD4eF5gH7iJ9kL0mN2oP4";
  assert.equal(tokenFromHash(`#token=${token}`), token);
  assert.equal(tokenFromHash(`token=${token}`), token);
  assert.equal(tokenFromHash(`#utm=x&token=${token}`), token);
});

test("reset links: a missing, cut or altered token is no token", () => {
  assert.equal(tokenFromHash(""), null);
  assert.equal(tokenFromHash("#"), null);
  assert.equal(tokenFromHash("#token="), null);
  assert.equal(tokenFromHash("#token=Zk3n0_q"), null); // cut short by a mail client
  assert.equal(tokenFromHash("#token=<script>alert(1)</script>xxxxxxxxxxxxxxx"), null);
});
