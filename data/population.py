"""Population model — ~1,000 personnel across 4-6 battalions (F09).

Structure is battalion > company > platoon. The allocator is arithmetic, not
random: it splits the requested headcount so that **every** unit at every level
holds at least :data:`data.spec.K_ANONYMITY` people, which is what makes the
TC-504 guard a property of the generator rather than a lucky draw.

Per-person attributes are drawn from a per-personnel RNG stream keyed on the
pseudonym, so adding a new attribute below never reshuffles anybody's existing
draws (F09 "Determinism & reseeding").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import rng_for
from . import spec as S


@dataclass
class Person:
    seq: int
    personnel_id: str
    pseudonym_id: str
    unit_id: str                 # battalion — what the backend aggregates on
    battalion_id: str
    company_id: str
    platoon_id: str
    rank: str
    age: int
    entry_age: int
    tenure_years: int
    marital_status: str
    dependents: int
    home_distance_km: float
    legal_name: str
    skill_tags: List[str]
    participant: bool
    cohort: str

    def to_row(self) -> Dict[str, Any]:
        return {
            "personnel_id": self.personnel_id,
            "pseudonym_id": self.pseudonym_id,
            "unit_id": self.unit_id,
            "battalion_id": self.battalion_id,
            "company_id": self.company_id,
            "platoon_id": self.platoon_id,
            "rank": self.rank,
            "age": self.age,
            "entry_age": self.entry_age,
            "tenure_years": self.tenure_years,
            "marital_status": self.marital_status,
            "dependents": self.dependents,
            "home_distance_km": self.home_distance_km,
            "legal_name": self.legal_name,
            "skill_tags": list(self.skill_tags),
            "participant": self.participant,
            "cohort": self.cohort,
        }


@dataclass
class Unit:
    unit_id: str
    level: str                   # battalion | company | platoon
    parent_id: Optional[str]
    size: int

    def to_row(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "level": self.level,
            "parent_id": self.parent_id,
            "size": self.size,
        }


@dataclass
class Population:
    people: List[Person] = field(default_factory=list)
    units: List[Unit] = field(default_factory=list)

    def by_pseudonym(self) -> Dict[str, Person]:
        return dict((p.pseudonym_id, p) for p in self.people)

    def unit_sizes(self) -> Dict[str, int]:
        return dict((u.unit_id, u.size) for u in self.units)


# ---------------------------------------------------------------------------
# Deterministic allocation
# ---------------------------------------------------------------------------


def split_headcount(total: int, target_parts: int, min_size: int) -> List[int]:
    """Split ``total`` into at most ``target_parts`` parts of >= ``min_size``.

    Reducing the number of parts (rather than emitting an undersized one) is
    exactly the k-anonymity guard: a unit that cannot reach ``min_size`` is
    never created in the first place.
    """
    if total <= 0:
        return []
    parts = max(1, min(target_parts, total // max(1, min_size)))
    base, remainder = divmod(total, parts)
    return [base + (1 if i < remainder else 0) for i in range(parts)]


def allocate(total: int) -> List[Tuple[str, str, str, int]]:
    """Return ``(battalion_id, company_id, platoon_id, size)`` for each platoon.

    The featured battalion (3rd Bn) is always first, so the persona lands in
    ``3BN`` / ``3BN-A`` / ``3BN-A1`` regardless of headcount.
    """
    order = [S.FEATURED_BATTALION] + [b for b in S.BATTALION_IDS if b != S.FEATURED_BATTALION]
    bn_sizes = split_headcount(total, len(order), S.MIN_BATTALION_SIZE)
    out: List[Tuple[str, str, str, int]] = []
    for bn_id, bn_n in zip(order, bn_sizes):
        coy_sizes = split_headcount(bn_n, len(S.COMPANY_LETTERS), S.MIN_COMPANY_SIZE)
        for letter, coy_n in zip(S.COMPANY_LETTERS, coy_sizes):
            coy_id = "{0}-{1}".format(bn_id, letter)
            plt_sizes = split_headcount(coy_n, S.PLATOONS_PER_COMPANY, S.MIN_PLATOON_SIZE)
            for idx, plt_n in enumerate(plt_sizes, start=1):
                out.append((bn_id, coy_id, "{0}{1}".format(coy_id, idx), plt_n))
    return out


def units_from_allocation(allocation: Sequence[Tuple[str, str, str, int]]) -> List[Unit]:
    bn_totals: Dict[str, int] = {}
    coy_totals: Dict[str, int] = {}
    coy_parent: Dict[str, str] = {}
    platoons: List[Unit] = []
    for bn_id, coy_id, plt_id, size in allocation:
        bn_totals[bn_id] = bn_totals.get(bn_id, 0) + size
        coy_totals[coy_id] = coy_totals.get(coy_id, 0) + size
        coy_parent[coy_id] = bn_id
        platoons.append(Unit(unit_id=plt_id, level="platoon", parent_id=coy_id, size=size))
    units = [Unit(unit_id=b, level="battalion", parent_id=None, size=n)
             for b, n in sorted(bn_totals.items())]
    units += [Unit(unit_id=c, level="company", parent_id=coy_parent[c], size=n)
              for c, n in sorted(coy_totals.items())]
    units += sorted(platoons, key=lambda u: u.unit_id)
    return units


# ---------------------------------------------------------------------------
# Attribute draws
# ---------------------------------------------------------------------------


def pick_weighted(rng, shares: Sequence[Tuple[Any, float]]) -> Any:
    roll = rng.random()
    acc = 0.0
    for value, weight in shares:
        acc += weight
        if roll < acc:
            return value
    return shares[-1][0]


def pick_index(rng, shares: Sequence[float]) -> int:
    roll = rng.random()
    acc = 0.0
    for idx, weight in enumerate(shares):
        acc += weight
        if roll < acc:
            return idx
    return len(shares) - 1


def married_prob(age: int) -> float:
    for upper, prob in S.MARRIED_PROB_BY_AGE:
        if age <= upper:
            return prob
    return S.MARRIED_PROB_BY_AGE[-1][1]


def build_person(
    seed: int,
    seq: int,
    battalion_id: str,
    company_id: str,
    platoon_id: str,
    participation_rate: float,
) -> Person:
    personnel_id = S.PERSONNEL_ID_FORMAT.format(seq=seq)
    pseudonym_id = S.PSEUDONYM_ID_FORMAT.format(seq=seq)
    rng = rng_for(seed, "person", pseudonym_id)

    rank = pick_weighted(rng, S.RANK_SHARES)
    lo, hi = S.AGE_RANGE_BY_RANK[rank]
    age = rng.randint(lo, hi)
    entry_age = rng.randint(*S.ENTRY_AGE_RANGE)
    tenure_years = max(S.MIN_TENURE_YEARS, age - entry_age)
    married = rng.random() < married_prob(age)
    shares = S.DEPENDENTS_SHARES_MARRIED if married else S.DEPENDENTS_SHARES_SINGLE
    dependents = pick_index(rng, shares)
    distance = round(rng.uniform(*S.HOME_DISTANCE_KM_RANGE), S.HOME_DISTANCE_KM_ROUND)
    legal_name = "{0} {1}".format(rng.choice(S.GIVEN_NAMES), rng.choice(S.SURNAMES))
    participant = rng.random() < participation_rate
    cohort = S.COHORT_AMBER if rng.random() < S.AMBER_BACKGROUND_RATE else S.COHORT_BASELINE

    return Person(
        seq=seq,
        personnel_id=personnel_id,
        pseudonym_id=pseudonym_id,
        unit_id=battalion_id,
        battalion_id=battalion_id,
        company_id=company_id,
        platoon_id=platoon_id,
        rank=rank,
        age=age,
        entry_age=entry_age,
        tenure_years=tenure_years,
        marital_status="married" if married else "single",
        dependents=dependents,
        home_distance_km=distance,
        legal_name=legal_name,
        skill_tags=["general"],
        participant=participant,
        cohort=cohort,
    )


def persona_person() -> Person:
    """DEMO-PERSONA-01 — ids, rank, age and unit pinned to backend/app/seed.py."""
    return Person(
        seq=0,
        personnel_id=S.PERSONA_PERSONNEL_ID,
        pseudonym_id=S.PERSONA_PSEUDONYM_ID,
        unit_id=S.PERSONA_UNIT_ID,
        battalion_id=S.PERSONA_UNIT_ID,
        company_id="{0}-{1}".format(S.PERSONA_UNIT_ID, S.COMPANY_LETTERS[0]),
        platoon_id="{0}-{1}1".format(S.PERSONA_UNIT_ID, S.COMPANY_LETTERS[0]),
        rank=S.PERSONA_RANK,
        age=S.PERSONA_AGE,
        entry_age=22,
        tenure_years=S.PERSONA_AGE - 22,
        marital_status="married",
        dependents=2,
        home_distance_km=850.0,     # matches the seeded deployment distance_km
        legal_name=S.PERSONA_LEGAL_NAME,
        skill_tags=list(S.PERSONA_SKILL_TAGS),
        participant=True,
        cohort=S.COHORT_PERSONA,
    )


def build_population(
    seed: int,
    personnel: int,
    participation_rate: float = S.PARTICIPATION_RATE_DEFAULT,
) -> Population:
    """Build the full population; slot 1 of ``3BN-A1`` is always the persona."""
    allocation = allocate(personnel)
    units = units_from_allocation(allocation)
    people: List[Person] = []
    seq = 1
    persona_placed = False
    for battalion_id, company_id, platoon_id, size in allocation:
        for _ in range(size):
            if not persona_placed:
                people.append(persona_person())
                persona_placed = True
                continue
            people.append(
                build_person(seed, seq, battalion_id, company_id, platoon_id, participation_rate)
            )
            seq += 1
    return Population(people=people, units=units)


def build_population_from_sizes(
    seed: int,
    sizes: Sequence[Tuple[str, str, str, int]],
    participation_rate: float = S.PARTICIPATION_RATE_DEFAULT,
) -> Population:
    """Escape hatch for tests: build a population from explicit unit sizes.

    Used by the TC-504 **negative** test to force a 4-person unit past the
    allocator and prove the validator refuses it.
    """
    units = units_from_allocation(sizes)
    people: List[Person] = []
    seq = 1
    for battalion_id, company_id, platoon_id, size in sizes:
        for _ in range(size):
            people.append(
                build_person(seed, seq, battalion_id, company_id, platoon_id, participation_rate)
            )
            seq += 1
    return Population(people=people, units=units)
