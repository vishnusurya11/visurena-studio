"""The story layer: the one question an episode answers, and the value each
shot turns.

Both rules come from the screenwriting craft, read 2026-09-12, and both explain
faults we had already measured without knowing their name:

  * **One question per episode, answered inside it.**  Jesse Armstrong's fourth
    season of Succession fixes the form -- "Today, can X do Y?" -- and answers
    it before the hour ends.  An episode with no such question has no reason to
    stop where it stops.

  * **No shot without a turn.**  McKee: mark the value at the open and again at
    the close; if they are the same, the scene exists to explain something, and
    explanation belongs inside another scene's picture.  This is the story-side
    statement of the fault we kept meeting as a RENDER fault: a shot whose value
    does not turn is a shot with nothing to photograph, and it comes back
    frozen.  The freeze was never the engine's idea.

Both are REPORTED, never refused.  Episode 1 was cut before either field
existed, and a story lint that raises would block a finished episode over a
rule its plan predates.

Episode 10 added four TEXT rules (docs/analysis/ep10_dq_synthesis.md, B), all
pure functions of the plan's own strings so `studio.plan_gates` can refuse on
them and `report` can print them with one mechanism:

  * the lead speaks his own words -- a narration line that REPORTS a present
    character's speech (`, he said`; `Young said so`; `He would send word`) is
    a dialogue line given to the narrator (`reported_speech`, `speakers_on`);
  * a name's first hearing in the series carries its role (`naked_names`);
  * a narration line adds what the picture cannot show (`overlap`);
  * the plan says where its question is answered (`report(..., answer=)`).
"""
from __future__ import annotations

import re

ARROW = "->"
"""How a turn is written: the value before, the value after."""

QUESTION = re.compile(r"^\s*today,\s*can\s+\S+.*\?\s*$", re.IGNORECASE)
"""Armstrong's form.  "Today" is what makes it answerable in one episode, and
"can" is what makes the answer yes or no rather than an essay."""


def question_shape(question: str) -> bool:
    """Is the episode's question in the form that can be answered by an ending?"""
    return bool(QUESTION.match(question or ""))


def sides(turn: str) -> tuple[str, str]:
    """The value before and after, lowercased and stripped."""
    before, _, after = (turn or "").partition(ARROW)
    return before.strip().lower(), after.strip().lower()


def turns(turn: str) -> bool:
    """A turn needs two DIFFERENT values, written either side of the arrow."""
    before, after = sides(turn)
    return bool(before and after and before != after)


def turnless(shots) -> list[int]:
    """The shots that declare no turn, or declare the same value on both sides."""
    return [shot.index for shot in shots if not turns(getattr(shot, "turn", ""))]


def report(spec_question: str, shots, answer: str = "") -> dict:
    """The story verdict: what is missing, said in one line, and never raised.

    `answer` is `Episode.answer` -- "shot N", "line N" or "" -- and the report
    says where the question lands so a reviewer can see whether the answer is
    a picture, a spoken sentence, or nowhere.  ep10's question ("can John
    Ferrier say no to the Prophet?") was answered by Doyle's own "But we
    haven't opposed him yet", which the plan cut; the viewer held "I won't
    knuckle under" (a yes) against a barred door (a no).  Reported, not refused."""
    empty = turnless(shots)
    ok = question_shape(spec_question)
    says = []
    if not ok:
        says.append('no episode question in the form "Today, can X do Y?"'
                    if not spec_question else f"the question does not answer in one episode: {spec_question!r}")
    if empty:
        says.append(f"{len(empty)} shots turn no value: {empty}")
    head = "; ".join(says) or "every shot turns a value and the episode asks one question"
    where = f"answered at: {answer}" if answer else "answered: nowhere"
    return {"question_ok": ok, "turnless": empty, "answer": answer, "passed": ok and not empty,
            "says": f"{head}; {where}"}


# ---- the lead speaks his own words -------------------------------------------

SAID = re.compile(r"\b([A-Z][a-z]+|[Hh]e|[Ss]he)\s+said\b")
"""`, he said` / `Young said so`: the speaker named outright.  `had never said
why` has no subject before `said` and is not a report."""

REPORTS = re.compile(r"\b([Hh]e|[Ss]he)\s+(?:would|should)\b")
"""Free indirect speech: `He would send Hope word` is Ferrier's sentence with
the quotation marks removed (ep10 line 24, over Ferrier's own face)."""


def reported_speech(text: str) -> str:
    """The speaker a narration line reports: "he", "she", a lowercased name
    token, or "" when the line reports nobody.

    MEASURED: six of ep10's narration lines (9, 11, 15, 24, 25, 28) against
    none in ep07 and ep09.  A `said` outranks a modal in the same line: "She
    should have a month, he said" reports HIM."""
    said = SAID.search(text or "")
    if said:
        return said.group(1).lower()
    modal = REPORTS.search(text or "")
    return modal.group(1).lower() if modal else ""


PRONOUN = {"he": re.compile(r"\b(he|his|him)\b", re.I),
           "she": re.compile(r"\b(she|her|hers)\b", re.I)}


def pronouns(shots) -> dict[str, str]:
    """{face: "he" | "she"} read off the plan itself: the pronouns its
    single-face shots use in frame, motion and at_rest for that face.

    MEASURED ep10: john_ferrier he 65 / she 3, brigham_young 38 / 0,
    lucy_ferrier 0 / 27; ep05 madame_sawyer 0 / 12.  A face with no single-face
    shot, or a tie, gets no pronoun, and a bare `he said` never resolves to it."""
    counts: dict[str, dict[str, int]] = {}
    for shot in shots:
        if len(shot.faces) != 1:
            continue
        text = " ".join([shot.frame, shot.motion, getattr(shot, "at_rest", "")])
        tally = counts.setdefault(shot.faces[0], {"he": 0, "she": 0})
        for word, pattern in PRONOUN.items():
            tally[word] += len(pattern.findall(text))
    return {who: max(t, key=t.get) for who, t in counts.items() if t["he"] != t["she"]}


def speakers_on(token: str, faces: list[str], pronoun_of: dict[str, str], names: dict[str, str]) -> list[str]:
    """The faces on a shot the reported speaker can be: the cast member who
    owns the name token, or every face whose pronoun is the bare one.  Two men
    in frame and a bare `he said` resolve to both -- whichever said it, his
    face is on screen with his mouth shut."""
    if token in names:
        return [face for face in faces if face == names[token]]
    return [face for face in faces if pronoun_of.get(face) == token]


# ---- a name's first hearing carries its role -----------------------------------

ROLE_NOUNS = ("prophet", "leader", "council", "hunter", "stranger", "young man", "farmer",
              "daughter", "elder", "son", "watchman", "sentinel", "mormon")
"""What a cold viewer needs beside a new name: "Jefferson Hope, the young man
who rode for Nevada".  ep10 said "Jefferson Hope" at 17 s as if known (0 hits
in ep09, where he is "a stranger") and "send Hope word" at 130 s, a homophone."""

ROLE = re.compile(r"\b(?:" + "|".join(ROLE_NOUNS) + r")s?\b", re.I)
ARTICLES = {"a", "an", "the"}
CAPITAL = re.compile(r"^[A-Z][a-z]+$")
WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]*|[,;:()\"]|--|—|–")
"""Words, and the punctuation that ends a name: "Nevada, John Ferrier" is two."""
SENTENCE = re.compile(r"[.!?]+")


def capital_runs(tokens: list[str]) -> list[tuple[int, list[str]]]:
    """(start, run) for every run of capitalised tokens that does not open the
    sentence -- the sentence-initial word is capitalised whatever it is."""
    out, run, start = [], [], 0
    for i, token in enumerate(tokens):
        if i and CAPITAL.match(token):
            start = start if run else i
            run.append(token)
        elif run:
            out.append((start, run))
            run = []
    return out + ([(start, run)] if run else [])


def names_in(text: str) -> list[str]:
    """Proper names in reading order, two-word names joined ("Jefferson Hope").

    A SINGLE capitalised word within two words of an article is a title or a
    common noun ("the Prophet", "a Gentile", "a free-born American"), never a
    name; a run of two or more is a name even after an article ("the Holy
    Four", "The Avenging Angels").  Places ("Nevada", "Utah") count: their
    first hearing is a first hearing."""
    out = []
    for sentence in SENTENCE.split(text or ""):
        tokens = [w.removesuffix("'s") for w in TOKEN.findall(sentence)]
        for start, run in capital_runs(tokens):
            titled = len(run) == 1 and ARTICLES & {t.lower() for t in tokens[max(0, start - 2):start]}
            if not titled:
                out.append(" ".join(run))
    return out


def heard(name: str, words: set[str]) -> bool:
    """Every token of the name has been said before ("Hope" after "Jefferson Hope")."""
    return all(token in words for token in name.split())


def naked_names(lines: list[str], earlier: list[str]) -> list[tuple[int, str]]:
    """(line index, name) for every name first heard in these lines, unheard in
    the earlier episodes' lines, whose first line carries no role noun."""
    known = set(re.findall(r"\b[A-Z][a-z]+\b", " ".join(earlier)))
    out = []
    for k, text in enumerate(lines):
        for name in names_in(text):
            if not heard(name, known) and not ROLE.search(text):
                out.append((k, name))
            known.update(name.split())
    return out


# ---- a narration line adds what the picture cannot show ------------------------

STOPWORDS = frozenset("""a an the and or but of to in on at by for from with into onto over under
across along off out up down through between behind before after above below beside
his her their its he she they him them it this that these those there here where when
while as than then so if not no nor is are was were be been being has have had do does
did will would shall should can could may might must one once own same very just only
also both each few more most other some such all any every either neither who whom
whose which what whole""".split())
"""Function words and pronouns: what is left is the nouns and verbs a picture
can or cannot show."""


def stem(word: str) -> str:
    """Enough of a stem to match "tightening" to "tighten" and "boots" to "boot"."""
    word = word.lower().replace("'s", "")
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3 and not word.endswith("ss"):
            return word[:-len(suffix)]
    return word


def content_words(text: str) -> set[str]:
    return {stem(w) for w in WORD.findall(text or "") if len(w) >= 3 and w.lower() not in STOPWORDS}


def overlap(line: str, shot_text: str) -> float:
    """The share of the line's content words already in its shot's text: 1.0 is
    a caption, 0.0 a line that adds only what the picture cannot show."""
    said = content_words(line)
    return len(said & content_words(shot_text)) / len(said) if said else 0.0
