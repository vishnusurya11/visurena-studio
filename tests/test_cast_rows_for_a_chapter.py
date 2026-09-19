"""refs.json carries ONE chapter's clothes per character (`pack_refs.character_row`),
so an episode rewrites the rows for its own chapter and its own cast, keeping each
row's display name and gender (ep02: Ogilvy's ch1 Inverness cape and smoking cap
would have reached a dawn on Horsell Common where he is bareheaded in a tweed suit)."""
import json

from studio import pack_refs


def card(tmp_path, who, by_chapter, wardrobe):
    (tmp_path / "analysis" / "characters").mkdir(parents=True, exist_ok=True)
    (tmp_path / "analysis" / "characters" / f"{who}.json").write_text(json.dumps(
        {"name": who.title(), "profile": {"physical": "A man.", "wardrobe": wardrobe,
                                          "wardrobe_by_chapter": by_chapter}}), encoding="utf-8")


def test_the_rows_carry_the_chapters_clothes_and_keep_the_names(tmp_path):
    card(tmp_path, "ogilvy", {"1": "night", "2": "dawn"}, {"night": "A cape.", "dawn": "A tweed suit."})
    old = [{"entity_id": "ogilvy", "kind": "character", "display": "Ogilvy", "gender": "male",
            "physical": "A man. Wearing: A cape."}]
    rows = pack_refs.rows_for(tmp_path, 2, ["ogilvy"], old)
    assert rows[0]["physical"] == "A man. Wearing: A tweed suit."
    assert rows[0]["display"] == "Ogilvy" and rows[0]["gender"] == "male"


def test_a_new_face_takes_the_display_and_gender_it_is_given(tmp_path):
    card(tmp_path, "henderson", {"2": "garden"}, {"garden": "Shirtsleeves."})
    rows = pack_refs.rows_for(tmp_path, 2, ["henderson"], [], {"henderson": ("Henderson", "male")})
    assert rows[0]["display"] == "Henderson" and rows[0]["gender"] == "male"


def test_a_row_outside_the_cast_is_kept_as_it_was(tmp_path):
    card(tmp_path, "ogilvy", {"2": "dawn"}, {"dawn": "A tweed suit."})
    wife = {"entity_id": "narrators_wife", "kind": "character", "display": "the Wife", "physical": "A woman."}
    rows = pack_refs.rows_for(tmp_path, 2, ["ogilvy"], [wife])
    assert wife in rows and len(rows) == 2
