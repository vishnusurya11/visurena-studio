# Skill: look back — read a drawn picture against its own prompt

You are shown one picture that was drawn from a prompt. You are never shown the
prompt, and you are never asked whether the picture is right.

## The one question

List what is in this picture; then say which of the asked nouns are absent.

- `seen`: every thing you can name in the picture, each as a short plain noun
  phrase — people, clothes, objects, animals, ground, sky, anything unexpected.
- `text`: true if any letters, words, numbers or captions appear anywhere,
  else false.
- `absent`: of the asked nouns you are given, the ones you cannot find.

Answer with strict JSON and nothing else.

## Rules

- Name what the pixels show. Do not guess from the period or the style what
  ought to be there.
- A thing partly hidden still counts as seen; a thing you cannot find is absent.
- Facial hair both ways: say "beard" or "moustache" when there is one, and say
  "clean-shaven face" when there is none.
- The judging is done by the code that asked; your list is the evidence.
