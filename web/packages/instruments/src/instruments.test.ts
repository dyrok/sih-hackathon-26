import { describe, expect, test } from "bun:test";

import { AGREE5, BANK, BY_ID, answerable } from "./bank";
import { MIN_MS_PER_ITEM, needsSafetyProtocol, scoreInstrument } from "./scoring";
import type { Answers } from "./scoring";

/**
 * The rule these tests exist to protect is the one in
 * docs/explanation/clinical-instruments.md §1: **validated instruments only,
 * never invented questions**. Everything else here is scoring arithmetic.
 */

const all = (id: string, value: number): Answers => {
  const inst = BY_ID[id]!;
  return Object.fromEntries(inst.items.map((i) => [i.id, value]));
};

describe("the bank is honest about what it ships", () => {
  test("every instrument names its published source", () => {
    for (const inst of BANK) {
      expect(inst.source).toMatch(/\d{4}/);
      expect(inst.source.length).toBeGreaterThan(20);
    }
  });

  test("a licensed instrument ships no item text at all", () => {
    const isi = BY_ID["ISI"]!;
    expect(isi.licence).toBe("licence_pending");
    expect(isi.items).toHaveLength(0);
    expect(isi.licenceNote).toContain("not reproduced");
    // …but its scoring and bands are implemented, so the licence is the only
    // thing standing between it and shipping.
    expect(isi.maxScore).toBe(28);
    expect(isi.bands.length).toBeGreaterThan(0);
  });

  test("answerable() excludes anything we cannot legally present", () => {
    const ids = answerable().map((i) => i.id);
    expect(ids).toContain("PHQ-9");
    expect(ids).toContain("GAD-7");
    expect(ids).toContain("PSS-10");
    expect(ids).not.toContain("ISI");
  });

  test("no Hindi rendering is claimed as adapted before the review runs", () => {
    for (const inst of BANK) expect(inst.adaptation).toBe("review_pending");
  });

  test("PSS-10 publishes no band, because it has no clinical cutoff", () => {
    expect(BY_ID["PSS-10"]!.bands).toHaveLength(0);
  });

  test("item counts match the published instruments", () => {
    expect(BY_ID["PHQ-9"]!.items).toHaveLength(9);
    expect(BY_ID["GAD-7"]!.items).toHaveLength(7);
    expect(BY_ID["PSS-10"]!.items).toHaveLength(10);
  });

  test("every item carries both languages", () => {
    for (const inst of BANK) {
      for (const item of [...inst.items, ...inst.validityItems]) {
        expect(item.en.length).toBeGreaterThan(3);
        expect(item.hi.length).toBeGreaterThan(3);
      }
    }
  });

  test("the validity probes are separate from the scored items", () => {
    for (const inst of BANK) {
      expect(inst.validityItems).toHaveLength(2);
      for (const probe of inst.validityItems) {
        expect(probe.validity).toBe("social_desirability");
        expect(inst.items.map((i) => i.id)).not.toContain(probe.id);
      }
    }
    expect(AGREE5.options).toHaveLength(5);
  });
});

describe("scoring", () => {
  test("PHQ-9 all-zero scores zero", () => {
    const s = scoreInstrument("PHQ-9", all("PHQ-9", 0), 60_000);
    expect(s.score).toBe(0);
    expect(s.answered).toBe(9);
    expect(s.bandKey).toBe("band.minimal");
  });

  test("PHQ-9 all-max reaches the published maximum", () => {
    const s = scoreInstrument("PHQ-9", all("PHQ-9", 3), 60_000);
    expect(s.score).toBe(27);
    expect(s.maxScore).toBe(27);
    expect(s.bandKey).toBe("band.severe");
  });

  test("GAD-7 bands break at the published anchors", () => {
    const inst = BY_ID["GAD-7"]!;
    const at = (total: number) => {
      // Distribute `total` across the seven items.
      const answers: Answers = {};
      let left = total;
      for (const item of inst.items) {
        const v = Math.min(3, left);
        answers[item.id] = v;
        left -= v;
      }
      return scoreInstrument("GAD-7", answers, 60_000);
    };
    expect(at(4).bandKey).toBe("band.minimal");
    expect(at(5).bandKey).toBe("band.mild");
    expect(at(10).bandKey).toBe("band.moderate");
    expect(at(15).bandKey).toBe("band.severe");
  });

  test("PSS-10 reverse-scores items 4, 5, 7 and 8", () => {
    const inst = BY_ID["PSS-10"]!;
    const reversed = inst.items.filter((i) => i.reverse).map((i) => i.id);
    expect(reversed).toEqual(["PSS-4", "PSS-5", "PSS-7", "PSS-8"]);

    // Answering 0 everywhere gives 4 reversed items at their maximum of 4.
    const zeros = scoreInstrument("PSS-10", all("PSS-10", 0), 60_000);
    expect(zeros.score).toBe(16);
    // Answering 4 everywhere gives the six forward items at 4 each.
    const fours = scoreInstrument("PSS-10", all("PSS-10", 4), 60_000);
    expect(fours.score).toBe(24);
  });

  test("a partly answered instrument scores only what was answered", () => {
    const inst = BY_ID["PHQ-9"]!;
    const answers: Answers = { [inst.items[0]!.id]: 3, [inst.items[1]!.id]: 2 };
    const s = scoreInstrument("PHQ-9", answers, 20_000);
    expect(s.score).toBe(5);
    expect(s.answered).toBe(2);
    expect(s.total).toBe(9);
  });

  test("an unknown instrument is refused, not silently scored", () => {
    expect(() => scoreInstrument("MADE-UP-7", {}, 1000)).toThrow();
  });
});

describe("validity flags — the faking is the finding", () => {
  test("identical answers across the instrument flag straight-lining", () => {
    const s = scoreInstrument("PHQ-9", all("PHQ-9", 1), 60_000);
    expect(s.flags.straight_lining).toBe(true);
  });

  test("varied answers do not flag straight-lining", () => {
    const inst = BY_ID["PHQ-9"]!;
    const answers: Answers = {};
    inst.items.forEach((item, i) => {
      answers[item.id] = i % 4;
    });
    const s = scoreInstrument("PHQ-9", answers, 60_000);
    expect(s.flags.straight_lining).toBe(false);
  });

  test("finishing faster than anyone could read flags too_fast", () => {
    const quick = scoreInstrument("PHQ-9", all("PHQ-9", 2), 9 * MIN_MS_PER_ITEM - 1);
    expect(quick.flags.too_fast).toBe(true);
    const considered = scoreInstrument("PHQ-9", all("PHQ-9", 2), 9 * MIN_MS_PER_ITEM + 1);
    expect(considered.flags.too_fast).toBe(false);
  });

  test("every item at the scale maximum flags all_max", () => {
    expect(scoreInstrument("PHQ-9", all("PHQ-9", 3), 60_000).flags.all_max).toBe(true);
    expect(scoreInstrument("PHQ-9", all("PHQ-9", 2), 60_000).flags.all_max).toBe(false);
  });

  test("maximally endorsing both social-desirability probes flags validity_fail", () => {
    const inst = BY_ID["PHQ-9"]!;
    const answers = all("PHQ-9", 1);
    for (const probe of inst.validityItems) answers[probe.id] = 4;
    expect(scoreInstrument("PHQ-9", answers, 60_000).flags.validity_fail).toBe(true);

    const honest = all("PHQ-9", 1);
    honest[inst.validityItems[0]!.id] = 4;
    honest[inst.validityItems[1]!.id] = 1;
    expect(scoreInstrument("PHQ-9", honest, 60_000).flags.validity_fail).toBe(false);
  });

  test("the probes never move the instrument score", () => {
    const inst = BY_ID["GAD-7"]!;
    const plain = all("GAD-7", 1);
    const withProbes = { ...plain };
    for (const probe of inst.validityItems) withProbes[probe.id] = 4;
    expect(scoreInstrument("GAD-7", withProbes, 60_000).score).toBe(
      scoreInstrument("GAD-7", plain, 60_000).score,
    );
  });
});

describe("the safety protocol routes to a human", () => {
  test("any endorsement of PHQ-9 item 9 triggers it", () => {
    const inst = BY_ID["PHQ-9"]!;
    for (const value of [1, 2, 3]) {
      const answers = all("PHQ-9", 0);
      answers[inst.items[8]!.id] = value;
      const s = scoreInstrument("PHQ-9", answers, 60_000);
      expect(s.item_9).toBe(value);
      expect(needsSafetyProtocol(s)).toBe(true);
    }
  });

  test("a zero on item 9 does not trigger it", () => {
    const s = scoreInstrument("PHQ-9", all("PHQ-9", 0), 60_000);
    expect(s.item_9).toBe(0);
    expect(needsSafetyProtocol(s)).toBe(false);
  });

  test("instruments without a safety item never carry item_9", () => {
    const s = scoreInstrument("GAD-7", all("GAD-7", 3), 60_000);
    expect(s.item_9).toBeUndefined();
    expect(needsSafetyProtocol(s)).toBe(false);
  });
});
