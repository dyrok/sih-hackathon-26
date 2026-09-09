/** One answer option on a response scale. `value` is the scored integer. */
export type ScaleOption = { value: number; labelKey: string };

export type Scale = {
  id: string;
  optionKeys: string[];
  options: ScaleOption[];
};

/**
 * Why an instrument might not be answerable in the app today. Being explicit
 * beats shipping a paraphrase: clinical-instruments.md §1 is unambiguous that a
 * paraphrased clone would violate the validated-instruments-only rule.
 */
export type LicenceStatus = "reproducible" | "licence_pending";

/** Whether the Hindi wording has been through the §3 adaptation pipeline. */
export type AdaptationStatus = "adapted" | "review_pending";

export type Item = {
  id: string;
  /** English stem, verbatim from the published instrument. */
  en: string;
  /** Romanised Hindi rendering. `adaptation` says how far it has been reviewed. */
  hi: string;
  /** Reverse-scored against the scale maximum (PSS-10 items 4, 5, 7, 8). */
  reverse?: boolean;
  /** Not part of the instrument score — a response-style probe (see §4). */
  validity?: "social_desirability";
};

export type Band = { min: number; max: number; labelKey: string };

export type Instrument = {
  id: "PHQ-9" | "GAD-7" | "PSS-10" | "ISI";
  nameKey: string;
  windowKey: string;
  scale: Scale;
  items: Item[];
  /** Extra probes appended to the flow; excluded from the instrument total. */
  validityItems: Item[];
  maxScore: number;
  /** Bands are shown to clinicians, never to the person taking it (F02). */
  bands: Band[];
  /** 1-based index of the self-harm item that triggers the safety protocol. */
  safetyItemIndex?: number;
  licence: LicenceStatus;
  adaptation: AdaptationStatus;
  source: string;
  licenceNote?: string;
};
