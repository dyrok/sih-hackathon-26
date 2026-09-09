import type { Instrument, Scale } from "./types";

/**
 * The instrument bank.
 *
 * Ground rule from docs/explanation/clinical-instruments.md: **validated
 * instruments only, never invented questions**. Consequences visible here:
 *
 * - PHQ-9 and GAD-7 carry their published stems. Pfizer released the PHQ/GAD
 *   family for reproduction without permission, so they ship in full.
 * - PSS-10 carries its published stems (Cohen, Kamarck & Mermelstein 1983),
 *   free for research and educational use, with items 4/5/7/8 reverse-scored.
 * - ISI is copyrighted (Bastien, Vallières & Morin 2001) and its items are NOT
 *   reproduced here. The flow, scoring and bands exist; the item text is gated
 *   behind `licence: "licence_pending"` and the UI says so plainly. Shipping a
 *   paraphrase would be exactly the failure the ground rule forbids.
 * - Hindi is marked `review_pending` for every instrument: the §3 pipeline
 *   (forward translation → synthesis → back-translation → expert committee →
 *   pilot) has not been run. English stays authoritative for scoring until it
 *   has been. The romanised Hindi below is a working rendering for usability
 *   testing, not a validated adaptation, and the app says that on screen.
 *
 * The two validity probes are genuine Marlowe-Crowne Social Desirability Scale
 * items (Crowne & Marlowe 1960), used as §4 describes: they are never added to
 * the instrument total, they only flag desirability bias.
 */

const FREQ4: Scale = {
  id: "freq4",
  optionKeys: ["scale.freq4.0", "scale.freq4.1", "scale.freq4.2", "scale.freq4.3"],
  options: [
    { value: 0, labelKey: "scale.freq4.0" },
    { value: 1, labelKey: "scale.freq4.1" },
    { value: 2, labelKey: "scale.freq4.2" },
    { value: 3, labelKey: "scale.freq4.3" },
  ],
};

const PSS5: Scale = {
  id: "pss5",
  optionKeys: ["scale.pss5.0", "scale.pss5.1", "scale.pss5.2", "scale.pss5.3", "scale.pss5.4"],
  options: [
    { value: 0, labelKey: "scale.pss5.0" },
    { value: 1, labelKey: "scale.pss5.1" },
    { value: 2, labelKey: "scale.pss5.2" },
    { value: 3, labelKey: "scale.pss5.3" },
    { value: 4, labelKey: "scale.pss5.4" },
  ],
};

export const AGREE5: Scale = {
  id: "agree5",
  optionKeys: [
    "scale.agree5.0",
    "scale.agree5.1",
    "scale.agree5.2",
    "scale.agree5.3",
    "scale.agree5.4",
  ],
  options: [
    { value: 0, labelKey: "scale.agree5.0" },
    { value: 1, labelKey: "scale.agree5.1" },
    { value: 2, labelKey: "scale.agree5.2" },
    { value: 3, labelKey: "scale.agree5.3" },
    { value: 4, labelKey: "scale.agree5.4" },
  ],
};

/** Crowne & Marlowe (1960), items 1 and 13 of the MC-SDS short form tradition. */
const VALIDITY_ITEMS = [
  {
    id: "MC-01",
    en: "I have never intensely disliked anyone.",
    hi: "Maine kabhi kisi ko sakht napasand nahi kiya.",
    validity: "social_desirability" as const,
  },
  {
    id: "MC-02",
    en: "I am always courteous, even to people who are disagreeable.",
    hi: "Main hamesha shishtachari rehta hoon, un logon ke saath bhi jo asahmat hain.",
    validity: "social_desirability" as const,
  },
];

const PHQ9: Instrument = {
  id: "PHQ-9",
  nameKey: "instrument.phq9.name",
  windowKey: "instrument.window",
  scale: FREQ4,
  maxScore: 27,
  safetyItemIndex: 9,
  licence: "reproducible",
  adaptation: "review_pending",
  source: "Kroenke, Spitzer & Williams (2001), J Gen Intern Med 16(9):606–613",
  items: [
    {
      id: "PHQ9-1",
      en: "Little interest or pleasure in doing things",
      hi: "Kaam karne mein kam ruchi ya khushi",
    },
    {
      id: "PHQ9-2",
      en: "Feeling down, depressed, or hopeless",
      hi: "Udaas, niraash ya bebas mehsoos karna",
    },
    {
      id: "PHQ9-3",
      en: "Trouble falling or staying asleep, or sleeping too much",
      hi: "Neend aane ya bane rehne mein dikkat, ya bahut zyada sona",
    },
    { id: "PHQ9-4", en: "Feeling tired or having little energy", hi: "Thakan ya kam urja mehsoos karna" },
    { id: "PHQ9-5", en: "Poor appetite or overeating", hi: "Bhookh kam lagna ya bahut zyada khana" },
    {
      id: "PHQ9-6",
      en: "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
      hi: "Khud ke baare mein bura lagna — ya lagna ki aap nakaam hain ya apne ya parivaar ko niraash kiya",
    },
    {
      id: "PHQ9-7",
      en: "Trouble concentrating on things, such as reading the newspaper or watching television",
      hi: "Kisi cheez par dhyan lagane mein dikkat, jaise akhbaar padhna ya TV dekhna",
    },
    {
      id: "PHQ9-8",
      en: "Moving or speaking so slowly that other people could have noticed — or the opposite, being so fidgety or restless that you have been moving around a lot more than usual",
      hi: "Itna dheere chalna ya bolna ki doosron ne dekha ho — ya iske ulat, itna bechain ki aap aam se zyada ghoomte rahe",
    },
    {
      id: "PHQ9-9",
      en: "Thoughts that you would be better off dead, or of hurting yourself in some way",
      hi: "Aise vichaar ki mar jaana behtar hoga, ya khud ko kisi tarah nuksaan pahunchane ke vichaar",
    },
  ],
  validityItems: VALIDITY_ITEMS,
  bands: [
    { min: 0, max: 4, labelKey: "band.minimal" },
    { min: 5, max: 9, labelKey: "band.mild" },
    { min: 10, max: 14, labelKey: "band.moderate" },
    { min: 15, max: 19, labelKey: "band.modsevere" },
    { min: 20, max: 27, labelKey: "band.severe" },
  ],
};

const GAD7: Instrument = {
  id: "GAD-7",
  nameKey: "instrument.gad7.name",
  windowKey: "instrument.window",
  scale: FREQ4,
  maxScore: 21,
  licence: "reproducible",
  adaptation: "review_pending",
  source: "Spitzer, Kroenke, Williams & Löwe (2006), Arch Intern Med 166(10):1092–1097",
  items: [
    { id: "GAD7-1", en: "Feeling nervous, anxious, or on edge", hi: "Ghabrahat, chinta ya tanav mehsoos karna" },
    {
      id: "GAD7-2",
      en: "Not being able to stop or control worrying",
      hi: "Chinta ko rok ya kaabu na kar paana",
    },
    { id: "GAD7-3", en: "Worrying too much about different things", hi: "Alag alag baaton ki bahut chinta karna" },
    { id: "GAD7-4", en: "Trouble relaxing", hi: "Aaram karne mein dikkat" },
    {
      id: "GAD7-5",
      en: "Being so restless that it is hard to sit still",
      hi: "Itna bechain hona ki chup-chaap baithna mushkil ho",
    },
    { id: "GAD7-6", en: "Becoming easily annoyed or irritable", hi: "Jaldi chidh jaana ya gussa aana" },
    {
      id: "GAD7-7",
      en: "Feeling afraid as if something awful might happen",
      hi: "Aisa dar lagna jaise kuch bura hone wala ho",
    },
  ],
  validityItems: VALIDITY_ITEMS,
  bands: [
    { min: 0, max: 4, labelKey: "band.minimal" },
    { min: 5, max: 9, labelKey: "band.mild" },
    { min: 10, max: 14, labelKey: "band.moderate" },
    { min: 15, max: 21, labelKey: "band.severe" },
  ],
};

const PSS10: Instrument = {
  id: "PSS-10",
  nameKey: "instrument.pss10.name",
  windowKey: "instrument.window.month",
  scale: PSS5,
  maxScore: 40,
  licence: "reproducible",
  adaptation: "review_pending",
  source: "Cohen, Kamarck & Mermelstein (1983), J Health Soc Behav 24(4):385–396",
  items: [
    {
      id: "PSS-1",
      en: "…been upset because of something that happened unexpectedly?",
      hi: "…kisi achanak hui baat se pareshan hue?",
    },
    {
      id: "PSS-2",
      en: "…felt that you were unable to control the important things in your life?",
      hi: "…laga ki aap apni zindagi ki zaroori cheezein kaabu nahi kar pa rahe?",
    },
    { id: "PSS-3", en: "…felt nervous and stressed?", hi: "…ghabrahat aur stress mehsoos kiya?" },
    {
      id: "PSS-4",
      en: "…felt confident about your ability to handle your personal problems?",
      hi: "…apni niji dikkatein sambhaalne par bharosa mehsoos kiya?",
      reverse: true,
    },
    {
      id: "PSS-5",
      en: "…felt that things were going your way?",
      hi: "…laga ki cheezein aapke hisaab se chal rahi hain?",
      reverse: true,
    },
    {
      id: "PSS-6",
      en: "…found that you could not cope with all the things that you had to do?",
      hi: "…paya ki jitna karna tha wo sab nahi kar paaye?",
    },
    {
      id: "PSS-7",
      en: "…been able to control irritations in your life?",
      hi: "…apni zindagi ki chidh ko kaabu kar paaye?",
      reverse: true,
    },
    { id: "PSS-8", en: "…felt that you were on top of things?", hi: "…laga ki sab kuch aapke haath mein hai?", reverse: true },
    {
      id: "PSS-9",
      en: "…been angered because of things that happened that were outside of your control?",
      hi: "…apne kaabu se bahar hui baaton par gussa aaya?",
    },
    {
      id: "PSS-10",
      en: "…felt difficulties were piling up so high that you could not overcome them?",
      hi: "…laga ki dikkatein itni badh gayi hain ki paar nahi kar sakte?",
    },
  ],
  validityItems: VALIDITY_ITEMS,
  // PSS-10 has no clinical cutoff by design (Cohen et al.): it is read against
  // population norms and the person's own trajectory, which is exactly how the
  // engine uses it. Publishing a band here would invent a cutoff.
  bands: [],
};

const ISI: Instrument = {
  id: "ISI",
  nameKey: "instrument.isi.name",
  windowKey: "instrument.window.sleep",
  scale: FREQ4,
  maxScore: 28,
  licence: "licence_pending",
  adaptation: "review_pending",
  source: "Bastien, Vallières & Morin (2001), Sleep Medicine 2(4):297–307",
  licenceNote:
    "ISI item text is copyrighted and is deliberately not reproduced in this repository. Scoring, bands and the flow are implemented; the items unlock when the licence is in place. A paraphrase would violate the validated-instruments-only rule (clinical-instruments.md §1).",
  items: [],
  validityItems: VALIDITY_ITEMS,
  bands: [
    { min: 0, max: 7, labelKey: "band.none" },
    { min: 8, max: 14, labelKey: "band.subthreshold" },
    { min: 15, max: 21, labelKey: "band.moderate" },
    { min: 22, max: 28, labelKey: "band.severe" },
  ],
};

export const BANK: Instrument[] = [PHQ9, GAD7, PSS10, ISI];

export const BY_ID: Record<string, Instrument> = Object.fromEntries(
  BANK.map((i) => [i.id, i]),
);

/** Only instruments we can legally and honestly present today. */
export function answerable(): Instrument[] {
  return BANK.filter((i) => i.licence === "reproducible" && i.items.length > 0);
}
