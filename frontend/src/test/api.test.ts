import { asList } from "../lib/api";

test("asList fail-closes on object payloads so Shell cannot crash", () => {
  expect(asList(undefined)).toEqual([]);
  expect(asList(null)).toEqual([]);
  expect(asList({ ok: true })).toEqual([]);
  expect(asList({ items: [{ id: 1 }] })).toEqual([{ id: 1 }]);
  expect(asList({ conversations: [{ id: "c1" }] })).toEqual([{ id: "c1" }]);
  expect(asList([{ id: "c1" }])).toEqual([{ id: "c1" }]);
});
