# Craft reference — period register (Victorian, 1887)

**Not a skill file.** The source for the period rules in `agents/skills/screenwriter.md`.

*A Study in Scarlet* is 1887. This is the reference for making Victorian speech sound
period **without pastiche** — and most of it is measured from the corpus rather than
asserted, because the received wisdom here is wrong in a specific, checkable way.

---

## 1. The governing principle

**Hilary Mantel, BBC Reith Lecture 5, "Adaptation" (2017).** The most useful sentence in
the whole domain:

> "**Pastiche is not creative. We don't need our characters to mouth the words of another
> century, but to possess the common knowledge of their era — so they don't say what they
> could never think.**"

The constraint is **on thought, not on vocabulary.** Her preceding image makes it
physical: put a modern woman in a properly weighted sixteenth-century dress and she
cannot stand any other way — "**Reality has a coercive force.** … It's the same with
dialogue."

Also hers, on the writer's position:

> "**The writer of history is a walking anachronism** … using today's techniques to try to
> know things about yesterday that yesterday didn't know itself. He must try to work
> authentically, hearing the words of the past, **but communicating in a language the
> present understands.**"

And on exposition, which is the classic period-fiction failure:

> "We all know how not to do it: '*Why masters, here comes the Lady Anne Boleyn, she who
> has supplanted the Spanish Queen Katherine…*' — **You can't have your people telling
> their contemporaries what they would already know.**"
> "**There's a lot of use in a stupid character, one who has to be told twice. There's more
> use in a stranger** — some newcomer who can ask the questions the reader wants to ask."
> "**You need to know ten times as much as you tell.**"

**Sarah Waters** names the same principle from the other side — *"I know it's an illusion,
obviously, but the whole point of writing a historical novel is to make the leap into a
slightly different mentality."* Her method is pure immersion: *"Steep yourself in the
writing of the time: fiction, journalism, diaries, letters. Try to absorb how people
thought and spoke."*

**Philip Gooden** (Historical Novel Society) supplies the two operational rules:

> "**All that care devoted to costumes and art-deco fittings and moustache trimmers but
> still the bubble of belief can be pricked with a single word.**"

> **The two-tier rule:** a later-coined word "is all right in a descriptive, non-dialogue
> passage, as author's 'commentary', but **an alternative expression should probably be
> found if the subject is being spoken about.**"

And the good news for us specifically:

> "**imitation becomes more feasible the closer the approach to the 21st century.
> Confirming this, there has been a long vogue for Victorian pastiche.**" — Palliser,
> Faber, Waters, Byatt. "the language conforms fairly closely to the style of the period,
> **but there is often an ironic tinge to it.**"

Gooden's cautionary case is, aptly, **Conan Doyle's own** *The White Company* (1891):
*"This is as artificial and lurid as Technicolor and it's not surprising that Doyle's
histories are almost forgotten now."* **Doyle himself committed the pastiche error — in
the medieval register.** He did not commit it in Holmes.

---

## 2. Contractions — the received wisdom is WRONG, with numbers

Measured by splitting each Gutenberg text into quoted dialogue vs narration and counting
all `n't` forms plus common pronoun contractions.

| novel | dialogue (per 10k words) | narration | ratio |
|---|---|---|---|
| Dickens, *Great Expectations* (1861) | **224** | 11 | 20× |
| Dickens, *Bleak House* (1853) | **175** | 7 | 25× |
| Gaskell, *North and South* (1855) | **174** | 1 | 174× |
| Trollope, *Barchester Towers* (1857) | **117** | 5 | 23× |
| Eliot, *Middlemarch* (1871) | **116** | 0.5 | 232× |
| Brontë, *Jane Eyre* (1847) | **49** | 0.4 | 122× |
| Austen, *Pride and Prejudice* (1813) | **4** | 0.2 | 20× |

**Four conclusions you can bank:**

1. **Writing contraction-free Victorian dialogue is not archaism; it is an error.**
   Victorian novelists contract in dialogue at 1.2–2.2% of all spoken words — one in
   every 45 to 90 words, comparable to modern fiction.
2. **The rule they actually observed was not "don't contract" but "contract in speech,
   not in formal prose."** The dialogue/narration split runs 20× to 200×.
3. **Austen is the outlier, not the model.** Writers absorb "period speech" from Austen
   adaptations and apply an Austen-level ban to an 1870s setting, producing dialogue
   **40× stiffer than Dickens's or Eliot's.** For a Victorian project, calibrate to
   Dickens/Gaskell/Eliot.
4. **Class signal:** `n't` forms dominate everywhere; pronoun forms (**I'm, it's, I've**)
   skew toward Dickens and Gaskell, who write working-class and Northern speakers.
   **Use pronoun contractions to mark down the register; keep only `n't` forms to keep a
   speaker genteel.**

### Doyle's own numbers — *A Study in Scarlet*, 822 speeches, 21,657 words of dialogue

| contracted | n | full form | n |
|---|---|---|---|
| don't | **39** | do not | 12 |
| didn't | **11** | did not | 8 |
| won't | **8** | will not | 4 |
| I'll | **20** | I shall | 14 |
| ain't | **10** | — | — |
| it's | 18 | it is | **58** |
| I'm | 10 | I am | **38** |
| I've | 6 | I have | **67** |

**The pattern is asymmetric, and the asymmetry is the actual period marker.** Negative
contractions *dominate* their full forms; pronoun+verb contractions are *outnumbered*.
Writing "do not" everywhere is the pastiche error; writing "I'm gonna" is the anachronism
error. **Sit exactly where Doyle sits.**

### Speech length — much shorter than people assume

- mean **26.3 words** per speech, **median 8**
- **60% of speeches are 10 words or fewer**; 77% ≤20; only 13% exceed 40

Stein's "over three sentences and you may be speechifying" is **already empirically true
of Doyle.** The long Holmes aria is the rare event, not the texture.

---

## 3. What actually carries the period flavour

Register markers in *A Study in Scarlet*'s dialogue: `sir` 20 · `Mr.` 31 · `Miss` 13 ·
`Doctor` 15 · `indeed` 6 · **`pray` 3 · `I beg` 3 · `beg your pardon` 1** · `by Jove` 2.
Modals: **`should` 51 · `shall` 43 · `ought` 39** · `whom` 5.

> **The period flavour is NOT carried by the courtesy words.** Three `pray` and one
> `beg your pardon` in 21,657 words. It is carried by the **modal verbs**
> (`shall`/`should`/`ought` — 133 occurrences) and by the **forms of address**.

That is the single most actionable finding here, and it inverts what a model will do by
default.

### Cross-corpus politeness formulas (whole-text counts)

| formula | Austen *P&P* | Dickens *Bleak House* | Trollope *Barchester* | Eliot *Middlemarch* | Doyle *Adventures* |
|---|---|---|---|---|---|
| "beg your pardon" | 5 | **21** | 3 | 5 | 0 |
| "if you please" | 3 | **46** | 10 | 7 | 3 |
| "much obliged" | 1 | 16 | 2 | 7 | 2 |
| "pray" (all) | 26 | 69 | 47 | 55 | 42 |
| "upon my word" | 8 | 5 | 6 | 5 | 0 |
| **"your obedient servant"** | **0** | **0** | **0** | **0** | **0** |

- **"I beg your pardon" and "if you please" are Dickensian and class-inflected** — they
  cluster where servants, clerks and tradespeople speak. Trollope's gentry barely use them.
- **"Pray"** is remarkably even across all corpora, ~2–3 per 10k words. The safest single
  marker: universal, unobtrusive, unmistakably not modern.
- **"Much obliged"** is a *Victorian* staple, essentially absent from Austen.

### "Your obedient servant" — an important corrective

Searched across Dickens, Trollope, Austen and Thackeray. **Every single hit is a letter
subscription. Not one is spoken dialogue.**

> Putting "your obedient servant" in a character's **mouth** is a gadzookery tell. It
> belongs to the epistolary register only.

### Subjunctive and archaic function words (dialogue only)

`if he were` 0–9 per book · `if it be` 0–5 · **`lest` 3–10** · `amongst` 0–7 ·
`whilst` 0–1.

The subjunctive **survives but is rare** — a handful per 100k words. Sprinkling "if he
were" through every conditional is over-marking. **"Lest" is the most reliably present of
the archaic-feeling function words.** "Amongst"/"whilst" are far rarer than pastiche
assumes.

---

## 4. Forms of address

**The eldest-daughter rule, and it is positional not absolute:** the eldest unmarried
daughter *present* is `Miss Bennet`; younger sisters are `Miss Elizabeth Bennet`. With no
sisters in the room, a younger sister may be `Miss Bennet`. Sons follow the same rule —
`Mr. Holmes` for the eldest, `Mr. Mycroft` for a younger brother.

**Christian names are an intimacy marker.** Only family, spouses, and the dearly loved use
first names, usually in private. Servants say `Master Sherlock` / `Miss Violet`. School
custom — address by surname — "persisted into manhood as an address for friends."

**Verified against the corpus** (*Adventures of Sherlock Holmes*, ~108k words):

| form | count |
|---|---|
| "Holmes" | 461 |
| "Watson" | 81 |
| "John" | 26 (mostly other characters) |
| **"my dear Watson"** | **3** |
| "sir" | 78 |

Two usable findings: the two closest friends in Victorian fiction address each other by
**bare surname**, essentially never by Christian name; and **"my dear Watson" appears
three times in the entire volume.** If dialogue is dense with it, that is itself a form of
gadzookery.

**From a period etiquette manual** (*Manners and Rules of Good Society*):

> "**A lady should not address her husband colloquially by his surname only**… The usual
> rule is for a wife to speak of her husband as 'Mr. Brown,' or 'My husband,' except to
> intimate friends, when the christian name only is frequently used."
> Military: address as "Colonel B.", "Major C." — "**and not as 'General,' 'Colonel,' or
> 'Major,' except by their very intimate friends.**"
> Royal: "**The Prince of Wales… should be addressed by the upper classes as 'Sir.'**"

**The exploitable rule: the closer you are, the plainer the address.** Intimates say
"Sir"; strangers say "Your Majesty." Inverting it is a fast way to mark an outsider — or
an author.

---

## 5. Class idiolect — Doyle marks it grammatically, not lexically

Constable John Rance and the Utah characters:

> "Ye see, when I got up to the door it was so still and so lonesome… **I ain't afeared**
> of anything."
> "No, sir, we **hain't**." / "**I hain't said none** since I was half the height o' that gun."
> "them ones that you used to say every night in the waggon when **we was** on the Plains."
> "she didn't say good-bye… if she was just **goin'** over to Auntie's for tea"

Markers: `hain't`/`ain't` · `ye` · `afeared` · `warn't` · `o'` · `goin'` · double negation
("hain't said none") · non-standard concord ("we was") · "them ones".

**Holmes and Watson use none of these.** That is the class axis, and it is free — it is
already in the source.

### Dickens's practice, and the calibration warning

Norman Page's taxonomy of speech-characterisation: **identification · parody · realistic ·
conventional**. And G. L. Brook's crucial observation — Dickens "made free use of dialect…
but **the dialects he uses are class rather than regional dialects.**"

> **Dickens reserves heavy idiolect for MINOR and comic characters.** Of the characters
> with marked speech, about three quarters are minor and ~60% negatively marked.
> Protagonists — Pip, David, Esther — speak near-standard.

**If you mark your lead's speech as heavily as Mrs Gamp's, you have miscalibrated.** Heavy
idiolect reads as caricature: exactly right for a Jingle, fatal for a hero.

---

## 6. The anachronism check — two tools, and the division of labour matters

**Google Ngram tests whether the STRING existed. The OED tests whether the SENSE existed.**
Ngram is the cheap bulk screen; the OED is the adjudicator.

Also worth knowing: **CLiC (University of Birmingham)** is a 19th-century fiction corpus
that natively **separates quoted speech from narration** — the purpose-built instrument
for exactly the questions this reference turns on.

### Measured, 1880s frequency per million (Google Books, en-2019)

| word | verdict for 1887 |
|---|---|
| okay | ❌ 1839 US, but reads as a howler in British Victorian dialogue |
| teenager | ❌ 1922 (earlier *teener* 1894) |
| boyfriend / girlfriend | ❌ romantic sense 1906 / 1922 |
| fingerprint | ❌ red flag — **and note, for a detective story** |
| **"focus on"** | ❌ **1934 — the word is 17th-century, the collocation is not** |
| **"contact him"** | ❌ noise level throughout the century. A Victorian **writes to**, **calls on**, **waits upon** |
| **relationship** (romantic) | ❌ that sense only from **1944** |
| **hopefully** (sentence adverb) | ❌ that use only from **1932** |
| **scientist** | ⚠️ coined 1834 but **absent from books until the mid-1860s** — in 1840 a character says *natural philosopher* |
| commute | ⚠️ common — in the sense of *commuting a sentence*, not travelling |
| detective / clue / suspect / cab / telegram | ✅ safe |

**The trap the etymology dictionary will not catch:** *"focus on"*, *"contact him"*,
*"relationship"*, *"stress"* and *"hopefully"* all pass a frequency test on the bare word
and still betray you, because the modern **sense** or **collocation** is twentieth-century.
**Check the collocation, not the word.**

Second Ngram limit: it is a *books* corpus, so colloquial speech is systematically
under-represented. Doyle's own `ain't` is the calibration case.

### The named failure modes

**Tushery** — Stevenson coined it about his own *Black Arrow*, in a letter to W. E. Henley,
Hyères, May 1883, verbatim:

> "**I turned me to — what thinkest 'ou? — to Tushery, by the mass! Ay, friend, a whole
> tale of tushery. And every tusher tushes me so free, that may I be tushed if the whole
> thing is worth a tush.**"

It names **lexical affectation specifically** — the archaic exclamation standing in for the
whole disease.

**Gadzookery** — first recorded 1950–55; earliest citation I could verify is 1957. **No
coiner is attributable.** Attributions to a 1958 TLS review, Alfred Duggan, Rose Macaulay
or Rosemary Sutcliff are all **unverified — do not repeat them.** Definition (Quinion):
novelists who introduce *prithee*, *zounds*, *gramercy*, *gadzooks* "are sometimes accused
by British literary critics of indulging in gadzookery."

**Forsoothery** — an established synonym of **unknown origin**. No coiner, no dated first
use.

---

## 7. DO / DON'T for 1887

**Do**
- Set **negative contractions to dominate** (`don't` > `do not`), **pronoun contractions to
  be the minority** (`I have` > `I've`). Doyle's ratios, §2.
- Lean on **`shall` / `should` / `ought`** — 133 occurrences in 21k words of dialogue.
  This carries more period weight than any courtesy formula.
- Keep the **median speech near 8 words.**
- Use `Mr.` / `Miss` / `sir` / `Doctor`; make a Christian name a **marked event**.
- Mark class through **grammar and elision** (`ain't`, `we was`, `them ones`, `goin'`, `o'`),
  and only on the characters Doyle marks.
- Use **`pray`** as the safest single period marker — sparingly.

**Don't**
- **Don't add archaism.** Nothing Doyle doesn't use is safe to add.
- **Don't sprinkle `pray` / `I beg`** — three uses each in the whole book. Over-formality
  is the commonest tell.
- **Don't put "your obedient servant" in anyone's mouth.** It is epistolary only.
- **Don't let anyone speak in the narrator's register.** Watson-as-narrator is far more
  Latinate than Watson-in-dialogue.
- **Don't trust a word because the string existed.** Check the *sense* and the
  *collocation*.
- Avoid `okay`, `teenager`, `boyfriend`/`girlfriend`, `fingerprint`, modern-sense
  `relationship`/`stress`/`focus on`, `contact` as a verb, sentence-adverb `hopefully`.

---

## 8. The adapter's method — Iannucci

The most useful adapter statement, from *The Personal History of David Copperfield*:

> "We tried to **pull as many [lines] as possible from Dickens**, if not from *Copperfield*
> then from **his other writings**."
> "his language is so modern that actually when you try and kind of replicate it, **it
> doesn't sound like you're trying to put on a kind of an old-fashioned style.**"
> "**It's the language of the book, the humour, not the story.** Too many adaptations throw
> everything else out and stick to the story. **The story is actually the least interesting
> part.**"

He lifted "the melancholy mad elephants" from *Hard Times* into a *Copperfield* script.

**For us: the line bank is the whole Holmes canon plus Doyle's other 1880s work**, not just
*A Study in Scarlet*. Harvest, then write new lines in that manner.

---

## GAPS

| gap | status |
|---|---|
| Andrew Davies's dialogue method | **no method statement found** — get Sarah Cardwell, *Andrew Davies* (Manchester UP, 2005) |
| Emma Thompson's *S&S* diaries | not online; needs the physical book |
| O'Brian's Author's Note on language | **not verifiable online** |
| George MacDonald Fraser on period language | **no primary source** — the commonly attributed claim is unsourced |
| "Gadzookery" first attestation | needs the OED entry itself |
| Mantel in the *Paris Review* | **checked — contains nothing on dialogue.** Use Reith Lecture 5. |
