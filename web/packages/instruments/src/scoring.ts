import { BY_ID } from "./bank";
import type { Instrument } from "./types";

export type Answers = Record<string, number>;

export type ValidityFlags = {
  /** Every scored item answered identically (Meade & Craig 2012). */
  straight_lining: boolean;
  /** Finished faster than anyone could have read the items. */
  too_fast: boolean;
  /** Every scored item at the scale maximum. */
  all_max: boolean;
  /** Both social-desirability probes maximally endorsed. */
  validity_fail: boolean;
};

export type Scored = {
  instrument: string;
  score: number;
  maxScore: number;
  /** PHQ-9 item 9 raw value — routes the human safety protocol, never an app-only response. */
  item_9?: number;
  answered: number;
  total: number;
  flags: ValidityFlags;
  bandKey: string | null;
};

/** ~1.6 s per item is already implausibly fast for a read-and-consider answer. */
export const MIN_MS_PER_ITEM = 1600;

function reverseValue(value: number, instrument: Instrument): number {
  const max = instrument.scale.options[instrument.scale.options.length - 1]!.value;
  return max - value;
}

export function scoreInstrument(
  instrumentId: string,
  answers: Answers,
  elapsedMs: number,
): Scored {
  const instrument = BY_ID[instrumentId];
  if (!instrument) throw new Error(`unknown instrument ${instrumentId}`);

  const scoredValues: number[] = [];
  let score = 0;
  for (const item of instrument.items) {
    const raw = answers[item.id];
    if (raw === undefined) continue;
    const value = item.reverse ? reverseValue(raw, instrument) : raw;
    score += value;
    scoredValues.push(raw);
  }

  const scaleMax = instrument.scale.options[instrument.scale.options.length - 1]!.value;
  const answered = scoredValues.length;
  const total = instrument.items.length;

  const validityValues = instrument.validityItems
    .map((i) => answers[i.id])
    .filter((v): v is number => v !== undefined);
  const validityMax = 4; // the agreement scale used for the probes

  const flags: ValidityFlags = {
    straight_lining: answered >= 3 && new Set(scoredValues).size === 1,
    too_fast: answered > 0 && elapsedMs > 0 && elapsedMs < answered * MIN_MS_PER_ITEM,
    all_max: answered >= 3 && scoredValues.every((v) => v === scaleMax),
    validity_fail:
      validityValues.length > 0 && validityValues.every((v) => v >= validityMax),
  };

  const item9 =
    instrument.safetyItemIndex !== undefined
      ? answers[instrument.items[instrument.safetyItemIndex - 1]?.id ?? ""]
      : undefined;

  let bandKey: string | null = null;
  for (const band of instrument.bands) {
    if (score >= band.min && score <= band.max) {
      bandKey = band.labelKey;
      break;
    }
  }

  return {
    instrument: instrument.id,
    score,
    maxScore: instrument.maxScore,
    ...(item9 !== undefined ? { item_9: item9 } : {}),
    answered,
    total,
    flags,
    bandKey,
  };
}

/** True when the safety protocol must run: PHQ-9 item 9 endorsed at all. */
export function needsSafetyProtocol(scored: Scored): boolean {
  return scored.item_9 !== undefined && scored.item_9 >= 1;
}
