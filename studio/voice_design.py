"""Casting a voice for each character, in the shape Qwen3-TTS VoiceDesign reads.

The blog's Multi-Attribute Control example is not prose -- it is a LABELLED
SHEET, one attribute per line.  That shape matters: the repo's old
`voice_instruct` wrote three sentences of prose capped at 40 words, and every
character came back sounding like the same narrator at a different age, because
prose lets the model average.  A sheet cannot average; each line is one
decision.

WHAT THE FIRST CAST GOT WRONG, measured on 19 rendered clips.  Holmes came back
at 238 Hz -- HIGHER than Lucy Ferrier at 186 and level with an old woman at 242
-- and audibly nasal, because his timbre line said "dry and thin with a reedy
edge".  It rendered exactly what it was told.  Three rules came out of that:

  1. EVERY LINE MUST NAME SOMETHING A MICROPHONE CAN CAPTURE.  "Sentences
     arriving already finished" and "certain of himself before he has finished
     speaking" are novel prose; a frequency, a word rate, a resonance and a
     direction of pitch movement are direction.  Personality says how it is
     DELIVERED, not what the character is like.
  2. NEVER COMPARE TO ANOTHER CHARACTER.  Watson's pitch read "sitting lower
     than his companion", and the model renders one voice at a time and has
     never heard Holmes.  Anchor to a number instead.
  3. AGE IS AN ATTRIBUTE.  The first sheet had no age at all, and age moves
     timbre further than almost anything else.

ACCENT IS NAMED, AND NAMED HARD.  `voice.DELIVERY` records that this model
drifts American when an accent is mentioned, and answers by refusing to mention
one -- but not naming an accent does not leave it unset, it leaves it GUESSED.
The fix is a stated accent plus an explicit negation, kept in one constant so a
single edit re-accents the whole cast.
"""
from __future__ import annotations

ATTRIBUTES = ("gender", "age", "pitch", "pace", "volume", "clarity",
              "fluency", "accent", "timbre", "emotion", "intonation", "personality")
"""The blog's Multi-Attribute Control sheet, plus the age it left implicit."""

LABEL = {"gender": "Gender", "age": "Age", "pitch": "Pitch", "pace": "Pace",
         "volume": "Volume", "clarity": "Clarity", "fluency": "Fluency",
         "accent": "Accent", "timbre": "Timbre", "emotion": "Emotion",
         "intonation": "Intonation", "personality": "Personality"}

RP = ("British English, Received Pronunciation, the English of educated London. "
      "British, NOT American. No American vowels.")
LONDON = ("British English, working-class London. "
          "British, NOT American. No American vowels.")
FRONTIER = ("American English, plain nineteenth-century frontier speech, "
            "flattened vowels, no drawl.")
PULPIT = "American English, formal nineteenth-century pulpit speech, measured and old-fashioned."
"""Four accents, each stated once so one edit re-accents everyone who shares it."""


class NotCast(KeyError):
    """Asked for a voice nobody has cast."""


CAST: dict[str, dict[str, str]] = {
    "sherlock_holmes": {
        "gender": "male", "age": "a man of about forty",
        "pitch": "low and deep, a bass-baritone around 95 Hz, never rising",
        "pace": "slow and controlled, about 120 words per minute, unhurried",
        "volume": "quiet and even, never raised",
        "clarity": "precisely articulated, crisp consonants, no slurring",
        "fluency": "completely fluent, no hesitation and no filler sounds",
        "accent": RP,
        "timbre": "deep and resonant, strong chest resonance, warm, NOT nasal, NOT thin",
        "emotion": "calm, detached, quietly certain",
        "intonation": "narrow range, falling at the end of every sentence",
        "personality": "composed and deliberate, a delivery that never hurries",
    },
    "john_watson": {
        "gender": "male", "age": "a man of about forty",
        "pitch": "moderate for a man, a baritone around 115 Hz",
        "pace": "moderate, about 135 words per minute, evenly spaced",
        "volume": "full and steady, well supported",
        "clarity": "clearly articulated, relaxed, rounded vowels",
        "fluency": "smooth, with brief pauses between sentences",
        "accent": RP,
        "timbre": "warm and round, strong chest resonance, a slight breathiness",
        "emotion": "calm, kind, mildly surprised",
        "intonation": "moderate range, gentle rise on questions",
        "personality": "steady and unhurried, a reassuring delivery",
    },
    "jefferson_hope": {
        "gender": "male", "age": "a man of about forty-five",
        "pitch": "very low, a bass around 85 Hz, dropping further at phrase ends",
        "pace": "very slow, about 95 words per minute, long pauses between phrases",
        "volume": "quiet and tightly controlled, never raised",
        "clarity": "articulate but roughened, consonants worn down",
        "fluency": "fluent in short blocks, then stopping completely",
        "accent": FRONTIER,
        "timbre": "gravelled and dry, rough vocal fry, cracked, little brightness",
        "emotion": "cold and level, grief held down under control",
        "intonation": "very narrow range, almost flat, no melodic movement",
        "personality": "implacable and patient, a delivery past persuading",
    },
    "lucy_ferrier": {
        "gender": "female", "age": "a young woman of about twenty",
        "pitch": "high for a woman, around 230 Hz, lifting at phrase ends",
        "pace": "quick, about 165 words per minute, animated",
        "volume": "moderate, dropping to near-whisper when frightened",
        "clarity": "clear and open, bright unguarded vowels",
        "fluency": "fluent and spontaneous, occasionally rushing",
        "accent": FRONTIER,
        "timbre": "clean and light, bright head resonance, no roughness at all",
        "emotion": "open and warm, unguarded",
        "intonation": "wide range, lively, rising often",
        "personality": "direct and spontaneous, an unrehearsed delivery",
    },
    "brigham_young": {
        "gender": "male", "age": "a man of about sixty",
        "pitch": "the lowest voice in the story, a deep bass around 78 Hz",
        "pace": "very slow and ceremonial, about 100 words per minute",
        "volume": "full and effortless, filling a room without strain",
        "clarity": "immaculate, every syllable deliberately placed",
        "fluency": "perfectly fluent, formal, rehearsed",
        "accent": PULPIT,
        "timbre": "rich, round and heavy, deep chest resonance, cold rather than warm",
        "emotion": "serene and immovable, threat delivered as kindness",
        "intonation": "measured wide rise and fall, the cadence of scripture",
        "personality": "unhurried and absolute, a delivery no one interrupts",
    },
    "john_ferrier": {
        "gender": "male", "age": "a man of about sixty",
        "pitch": "low, around 90 Hz, dropping hard on a refusal",
        "pace": "slow and stubborn, about 105 words per minute, planting each word",
        "volume": "strong, rising sharply when defied",
        "clarity": "blunt, some consonants swallowed",
        "fluency": "halting, sentences assembled as they are spoken",
        "accent": FRONTIER,
        "timbre": "coarse and gravelly, heavy rasp, worn at the bottom",
        "emotion": "hard and protective, anger close to the surface",
        "intonation": "narrow range, falling hard at the end",
        "personality": "obstinate and weathered, an unafraid delivery",
    },
    "joseph_stangerson": {
        "gender": "male", "age": "a man of about forty",
        "pitch": "moderate, around 110 Hz, unvarying",
        "pace": "even, about 125 words per minute, reciting rather than speaking",
        "volume": "moderate and controlled, never rising",
        "clarity": "precise and cold, formal diction",
        "fluency": "wholly fluent, the fluency of doctrine repeated often",
        "accent": PULPIT,
        "timbre": "flat and dry, thin chest resonance, no colour",
        "emotion": "impersonal, neither angry nor kind",
        "intonation": "very narrow range, closing each sentence flat",
        "personality": "humourless and certain, a delivery that never doubts",
    },
    "enoch_j_drebber": {
        "gender": "male", "age": "a man of about forty-five",
        "pitch": "moderate, around 120 Hz, sliding unsteadily",
        "pace": "uneven, slurring then lurching to about 170 words per minute",
        "volume": "too loud, poorly controlled",
        "clarity": "smeared, consonants collapsing into each other",
        "fluency": "broken, losing the thread and restarting",
        "accent": FRONTIER,
        "timbre": "thick and wet, heavy throat resonance, muffled",
        "emotion": "leering good humour turning abruptly to spite",
        "intonation": "wandering and unstable, ending nowhere",
        "personality": "careless and unguarded, a slurred delivery",
    },
    "arthur_charpentier": {
        "gender": "male", "age": "a young man of about twenty-five",
        "pitch": "high for a man, a light tenor around 150 Hz, rising under stress",
        "pace": "fast, about 185 words per minute, tumbling",
        "volume": "raised throughout, poorly held down",
        "clarity": "clear but hurried, swallowing word endings",
        "fluency": "disrupted, breaking off and restarting",
        "accent": RP,
        "timbre": "bright and unseasoned, thin chest resonance",
        "emotion": "agitated, angry and frightened at once",
        "intonation": "wide range, sharply rising, protesting",
        "personality": "hot and unguarded, an over-fast delivery",
    },
    "g_lestrade": {
        "gender": "male", "age": "a man of about forty",
        "pitch": "moderate, around 130 Hz, pushing upward when insistent",
        "pace": "quick, about 175 words per minute, rushing",
        "volume": "raised a little too much, pushing for attention",
        "clarity": "sharp but clipped, swallowing the ends of words",
        "fluency": "fluent but self-interrupting, restarting mid-sentence",
        "accent": LONDON,
        "timbre": "narrow and metallic, forward and slightly nasal, thin",
        "emotion": "self-satisfied, turning defensive",
        "intonation": "wide range, rising and insistent",
        "personality": "eager and competitive, an argumentative delivery",
    },
    "tobias_gregson": {
        "gender": "male", "age": "a man of about forty-five",
        "pitch": "moderate-low, around 105 Hz",
        "pace": "brisk, about 150 words per minute, businesslike",
        "volume": "loud and confident, well projected",
        "clarity": "firm and well-formed, official diction",
        "fluency": "smooth and practised",
        "accent": LONDON,
        "timbre": "solid and broad, full chest resonance, slightly blustering",
        "emotion": "pleased with himself, brisk",
        "intonation": "moderate range, level and declarative",
        "personality": "smooth and assured, a briefing delivery",
    },
    "john_rance": {
        "gender": "male", "age": "a man of about thirty-five",
        "pitch": "low, around 100 Hz",
        "pace": "slow and plodding, about 110 words per minute",
        "volume": "comfortable and steady, no urgency",
        "clarity": "loose, dropped aitches, informal",
        "fluency": "rambling, circling back",
        "accent": LONDON,
        "timbre": "thick and stolid, heavy throat resonance, dull",
        "emotion": "pleased with himself, mildly aggrieved",
        "intonation": "narrow range, wandering, trailing off",
        "personality": "unhurried and self-important, a meandering delivery",
    },
    "madame_sawyer": {
        "gender": "female", "age": "an old woman of about seventy",
        "pitch": "high and unsteady, around 250 Hz, wavering",
        "pace": "slow and doddering, about 90 words per minute",
        "volume": "thin and weak, hard to catch",
        "clarity": "mumbled, words half-formed",
        "fluency": "wavering, losing the thread",
        "accent": LONDON,
        "timbre": "reedy and cracked, heavy tremor, very little chest resonance",
        "emotion": "pitiable and grateful, laid on a little thick",
        "intonation": "wide wavering range, sing-song and pleading",
        "personality": "frail and rambling, a performed delivery",
    },
    "stamford": {
        "gender": "male", "age": "a young man of about twenty-eight",
        "pitch": "moderate-high for a man, around 140 Hz",
        "pace": "quick and chatty, about 170 words per minute",
        "volume": "easy and sociable, unforced",
        "clarity": "clear and casual",
        "fluency": "fluent and unguarded, running ahead of itself",
        "accent": RP,
        "timbre": "bright and light, moderate chest resonance, friendly",
        "emotion": "amused, faintly conspiratorial",
        "intonation": "wide range, lively and rising",
        "personality": "sociable and quick, a gossiping delivery",
    },
    "unnamed_retired_marine_sergeant": {
        "gender": "male", "age": "a man of about fifty-five",
        "pitch": "low, around 95 Hz, settled",
        "pace": "steady, about 125 words per minute, reporting",
        "volume": "strong and even, parade-ground projection",
        "clarity": "crisp and disciplined",
        "fluency": "economical, no wasted words",
        "accent": LONDON,
        "timbre": "solid and weathered, firm chest resonance",
        "emotion": "calm and respectful, entirely unbothered",
        "intonation": "narrow range, ending flat",
        "personality": "plain and dependable, a matter-of-fact delivery",
    },
    "unnamed_cab_driver": {
        "gender": "male", "age": "a man of about forty",
        "pitch": "moderate, around 125 Hz",
        "pace": "brisk and impatient, about 165 words per minute",
        "volume": "raised over street noise",
        "clarity": "clipped and careless",
        "fluency": "blunt, short phrases",
        "accent": LONDON,
        "timbre": "coarse and open, rough edge, weathered",
        "emotion": "indifferent, mildly put out",
        "intonation": "narrow range, falling",
        "personality": "quick and transactional, an incurious delivery",
    },
    "unnamed_constable": {
        "gender": "male", "age": "a man of about thirty",
        "pitch": "low, around 100 Hz, big-chested",
        "pace": "deliberate, about 115 words per minute, official",
        "volume": "loud and authoritative",
        "clarity": "firm, carefully correct",
        "fluency": "stiff, choosing formal words",
        "accent": LONDON,
        "timbre": "broad and heavy, deep chest resonance",
        "emotion": "impassive, faintly officious",
        "intonation": "narrow range, level and declarative",
        "personality": "dutiful and literal, a by-the-book delivery",
    },
    "unnamed_railway_porter": {
        "gender": "male", "age": "a man of about thirty-five",
        "pitch": "moderate, around 135 Hz, hoarse at the top",
        "pace": "hurried, about 180 words per minute",
        "volume": "raised, shouting across a platform",
        "clarity": "shouted and blurred",
        "fluency": "fragmentary, working phrases only",
        "accent": LONDON,
        "timbre": "worn and hoarse, rasping from calling out",
        "emotion": "harried, unbothered",
        "intonation": "wide range, rising calls, abrupt endings",
        "personality": "busy and brusque, a shouted delivery",
    },
    "unnamed_servant": {
        "gender": "female", "age": "a young woman of about eighteen",
        "pitch": "high for a woman, around 245 Hz, small",
        "pace": "hesitant, about 140 words per minute, quickening when nervous",
        "volume": "quiet and apologetic",
        "clarity": "soft, half-swallowed",
        "fluency": "faltering, breaking off",
        "accent": LONDON,
        "timbre": "light and thin, little chest resonance, breathy",
        "emotion": "anxious, eager not to give offence",
        "intonation": "wide range, rising, everything a question",
        "personality": "timid and watchful, a deferring delivery",
    },
    "unnamed_hunter_companion": {
        "gender": "male", "age": "a man of about forty",
        "pitch": "low, around 92 Hz",
        "pace": "slow and sparing, about 100 words per minute, long silences",
        "volume": "low and carrying, pitched not to travel far",
        "clarity": "blunt, worn down",
        "fluency": "terse, long gaps between phrases",
        "accent": FRONTIER,
        "timbre": "dry and dusty, rough grain, little brightness",
        "emotion": "wary and unsentimental",
        "intonation": "very narrow range, no lift anywhere",
        "personality": "hard and practical, a sparing delivery",
    },
    "group_mormons": {
        "gender": "male", "age": "grown men of mixed age",
        "pitch": "many low male voices together, centred around 90 Hz",
        "pace": "slow and unified, about 95 words per minute, the pace of a chant",
        "volume": "swelling and heavy, a wall of sound",
        "clarity": "blurred by numbers, the words still legible",
        "fluency": "perfectly together, rehearsed by repetition",
        "accent": PULPIT,
        "timbre": "massed and resonant, no individual audible, deep and cavernous",
        "emotion": "righteous and implacable",
        "intonation": "wide liturgical rise and fall",
        "personality": "collective and certain, a chanted delivery",
    },
    "group_fugitives": {
        "gender": "male", "age": "grown men of mixed age",
        "pitch": "several ragged voices around 130 Hz, broken by exhaustion",
        "pace": "urgent and uneven, about 175 words per minute, overlapping",
        "volume": "hushed and pressed down, afraid of carrying",
        "clarity": "hoarse and half-formed",
        "fluency": "fragmentary, cut off by breathing",
        "accent": FRONTIER,
        "timbre": "dry, cracked and thirsty, rasping",
        "emotion": "fear held just short of panic",
        "intonation": "wide range, rising and unfinished",
        "personality": "desperate and hunted, a breathless delivery",
    },
    "group_two_detectives": {
        "gender": "male", "age": "men of about forty",
        "pitch": "two male voices around 110 and 130 Hz, one fuller and one thinner",
        "pace": "brisk and interrupting, about 165 words per minute",
        "volume": "raised, competing",
        "clarity": "official diction, sharpened by rivalry",
        "fluency": "fluent and overlapping",
        "accent": LONDON,
        "timbre": "one broad and blustering, one narrow and metallic",
        "emotion": "competitive self-satisfaction",
        "intonation": "moderate range, insistent and declarative",
        "personality": "territorial and quick, a talking-over delivery",
    },
}

CHECK_SENTENCE = ("I have looked at this a long while, and I know now what it is. "
                  "You may think what you like of me, but you will hear me out first.")
"""The one passage every cast voice speaks, so the VOICE is the only variable.
The same reason the emotion bank shares a baseline (`voice_bank.BASELINE`)."""

FEELING: dict[str, dict[str, str]] = {
    "calm": {},
    "urgent": {
        "emotion": "pressed and alarmed, something happening right now",
        "pace": "fast, about 180 words per minute, no space between phrases",
        "volume": "raised and pushing",
        "intonation": "clipped and rising, urging",
    },
    "grieving": {
        "emotion": "open grief, the voice breaking and being pulled back",
        "pace": "slow, about 90 words per minute, stopping to steady itself",
        "volume": "quiet, thinning almost to nothing",
        "intonation": "falling and unsupported, sentences dying out",
    },
    "threatening": {
        "emotion": "cold controlled menace, promise rather than threat",
        "pace": "very slow, about 85 words per minute, every word placed",
        "volume": "quiet, drawing the listener in rather than pushing",
        "intonation": "flat and level, landing hard on the last word",
    },
}
"""How a designed voice is redirected without recasting it.

The sheet already HAS an Emotion line, so a feeling is not a second instruct
bolted on -- it is the same decisions with four of them overwritten.  Which is
why `calm` is empty: it is the sheet as cast."""


def sheet(character: str, feeling: str = "calm") -> dict[str, str]:
    """The decisions cast for one character, redirected by a feeling."""
    if character not in CAST:
        raise NotCast(f"{character} has no voice cast in CAST")
    if feeling not in FEELING:
        raise NotCast(f"{feeling!r} is not one of {tuple(FEELING)}")
    return {**CAST[character], **FEELING[feeling]}


def instruct(character: str, feeling: str = "calm") -> str:
    """The cast sheet as Qwen3-TTS VoiceDesign reads it: one attribute per line."""
    voice = sheet(character, feeling)
    return "\n".join(f"{LABEL[a]}: {voice[a].rstrip('.')}." for a in ATTRIBUTES)


def distinctions(one: str, other: str) -> list[str]:
    """Which attributes two characters were cast differently on.

    A casting sheet earns nothing if two voices agree on nine lines out of
    twelve, and prose hides that; this counts it."""
    left, right = sheet(one), sheet(other)
    return [a for a in ATTRIBUTES if left[a] != right[a]]


def cast_list() -> list[str]:
    """Everyone with a voice, in casting order."""
    return list(CAST)
