"""The engineering tutorial, as one chapter per module.

Splitting the tutorial into files makes each chapter reviewable in a diff and
keeps the numbering local to its chapter.  Prose stays in Python rather than
plain Markdown because every chapter interleaves live results -- the calculated
phase envelope, the current run's difference points, the closure residuals --
and a worked example built from the reader's own inputs is worth more than the
same algebra restated.
"""

from dataclasses import dataclass
from typing import Any

import streamlit as st

from src.tutorial import (
    ch00_nomenclature,
    ch01_overview,
    ch02_equilibrium,
    ch03_flash,
    ch04_mccabe,
    ch05_ponchon,
    ch06_equipment,
    ch07_safety,
    ch08_validation,
)


@dataclass
class TutorialState:
    """Live results passed to every chapter so examples use the reader's run."""

    vle: Any = None
    column: Any = None
    z_F: float | None = None
    feed: Any = None
    P: float | None = None
    sizing_hint: str = ""


CHAPTERS = (
    ("0 · Nomenclature, conventions, and how to read the code", ch00_nomenclature),
    ("1 · Map of the problem and modelling assumptions", ch01_overview),
    ("2 · Phase equilibrium and the NRTL model", ch02_equilibrium),
    ("3 · Flash calculations", ch03_flash),
    ("4 · McCabe-Thiele: derivation, stepping, and limits", ch04_mccabe),
    ("5 · Ponchon-Savarit: the enthalpy-composition construction", ch05_ponchon),
    ("6 · Equipment sizing, utilities, and economics", ch06_equipment),
    ("7 · Safe operation and independent protection layers", ch07_safety),
    ("8 · Validation, acceptance criteria, and references", ch08_validation),
)


def render_tutorial(vle_data=None, column=None, z_feed=None, feed_state=None,
                    pressure=None) -> None:
    """Render the whole tutorial.  It never alters a calculation."""
    st.markdown("### Engineering tutorial — from phase equilibrium to a safe column")
    st.caption(
        "An educational design guide. It is not a replacement for validated "
        "property packages, relief-system design, HAZOP/LOPA, licensed "
        "pressure-vessel design, or a process-safety review."
    )

    state = TutorialState(
        vle=vle_data,
        column=column,
        z_F=z_feed,
        feed=feed_state,
        P=pressure,
    )

    st.markdown(
        "Chapters build on each other: each derivation uses results the previous "
        "chapter established, and equations are numbered so they can be referred "
        "to by number. Where a derivation ends, a **worked example** substitutes "
        "the current run's own numbers into the equation just obtained."
    )

    for title, module in CHAPTERS:
        with st.expander(title, expanded=False):
            module.render(state)
