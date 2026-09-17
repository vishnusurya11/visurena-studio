"""The sheet builder after episode 10 (docs/analysis/ep10_dq_synthesis.md, section D).

Measured on ep10's 48 cells by the storyboard analyst:

  D1  the four single-panel redraws lost their size word: Q13 0.25 -> 0.20 and
      Q25 0.66 -> 0.36 face height, and their takes are the episode's two worst.
      A sheet panel opens "Panel k - CLOSE, camera ..."; a single opened with the
      bare frame.
  D3  the ladder clause was obeyed 4/12: it named the front door in shots that
      face away from it (Q19, Q20) and asked for a thumbnail porch in a panel
      whose own at_rest says a hand (Q03).  Six of fourteen alternates named a
      non-object as their `{thing}`: "the black", "a line", "the lamp warm",
      "the deep-set eyes hard".
  D5  Q26_0 and its alternate Q26_0A read 0.718, over ALIKE 0.70, and the report
      on disk said `duplicates: []`.  An alternate feeds no take, so the pair is
      reported and buys no $0.13 strict re-roll.
"""
from PIL import Image

from studio import episode_seq_board as sq
from studio.episode_spec import Setup

PATH = Setup(described="The shingly path up to a log villa on a June morning.",
             landmark="the porch of the log house", landmark_at="far_end",
             landmark_size="is half the height of the frame",
             route="from the gate up the shingly path to the porch step")
DOORWAY = Setup(described="The porch step of the log villa.", landmark="the open front door",
                landmark_at="start", landmark_size="fills the frame",
                route="from the porch step down the shingly path to the gate")
TRAIL = Setup(described="A mountain trail by night.", landmark="the ridge line against the moonlit sky",
              landmark_at="far_end", landmark_size="is half the height of the frame",
              route="from the near bend of the trail along the rock shoulder to the far bend under the ridge")


def seg(shot, size="medium", path=0.3, frame="Two men on the path.", **kw):
    base = {"shot": shot, "sub": 0, "size": size, "path": path, "faces": [], "frame": frame,
            "camera": "on the path at a standing man's eye, a 35mm lens", "at_rest": "",
            "motion": "he walks on", "end_frame": "", "changed": "", "crowd": ""}
    return base | kw


# ---- D1  a single opens with its size word ----------------------------------

def test_single_picture_opens_with_size_word():
    close = seg(25, size="close", frame="Close on John Ferrier's bearded profile in the lamplight.")
    assert sq.single_picture(close, PATH).startswith("CLOSE, camera on the path")
    mcu = seg(13, size="medium_close", frame="Medium close on Brigham Young from above.")
    assert sq.single_picture(mcu, PATH).startswith("MEDIUM CLOSE-UP, camera on the path")


def test_the_single_prompt_s_picture_block_carries_the_size_word_and_the_at_rest():
    panel = seg(25, size="close", frame="Close on John Ferrier's bearded profile.",
                at_rest="His profile fills the CENTRE from the beard at the BOTTOM edge to the hair at the TOP.")
    text = sq.single(panel, PATH, {}, "1:1")
    picture = text.split("THE PICTURE\n")[1].split("\n\n")[0]
    assert picture.startswith("CLOSE, camera")
    assert "In frame: Close on John Ferrier's bearded profile." in picture
    assert "This is the instant BEFORE the action: His profile fills the CENTRE" in picture


def test_a_single_without_a_camera_still_opens_with_the_size_word():
    assert sq.single_picture(seg(3, size="wide", camera=""), PATH).startswith("WIDE. In frame:")


# ---- D3a  the ladder names a landmark that is in the frame --------------------

def test_landmark_head_is_the_noun_before_the_first_preposition():
    assert sq.landmark_head("the porch of the log house") == "porch"
    assert sq.landmark_head("the oil lamp on the pine table") == "lamp"
    assert sq.landmark_head("the open front door") == "door"
    assert sq.landmark_head("the Bunsen lamp's blue flame on the bench") == "flame"
    assert sq.landmark_head("") == ""


def test_a_compound_landmark_is_found_by_either_half():
    assert sq.landmark_in("the low moon behind the ridge at the right", "the ridge line against the moonlit sky")
    assert sq.landmark_in("the porch of the log villa", "the porch of the log house")
    assert sq.landmark_in("two porches up the hill", "the porch of the log house")
    assert not sq.landmark_in("Brigham Young's black-coated back going down the path", "the open front door")
    assert not sq.landmark_in("the blue sky over the trail", "the Bunsen lamp's blue flame on the bench")


def test_ladder_only_when_landmark_in_frame():
    """ep10 Q19/Q20: "the open front door the height of a thumbnail" printed on
    two panels whose camera faces AWAY from the door, down the path to the gate."""
    away = seg(20, size="wide", path=0.9,
               frame="Wide down the shingly path from the porch step to the open gate, a small black figure at it.")
    assert sq.ladder_clause(away, DOORWAY) == ""
    assert not sq.on_route(away, DOORWAY)
    back = seg(16, size="medium", path=0.0, frame="Brigham Young turned back on the threshold in the open door.")
    assert sq.ladder_clause(back, DOORWAY).strip() == "The open front door fills the frame."
    assert sq.on_route(back, DOORWAY)


def test_the_order_block_lists_only_panels_that_see_the_landmark():
    panels = [seg(19, size="medium", path=0.6, frame="His back going down the path."),
              seg(16, size="medium", path=0.0, frame="Turned back on the threshold in the open door.")]
    _group, route, _grid = sq.sheets(panels, DOORWAY, "1:1")[0]
    assert route == [2]


# ---- D3b  an alternate's {thing} is a thing -----------------------------------

def test_alt_thing_is_a_noun():
    """Six of ep10's fourteen alternates named an adjective tail as their object."""
    assert sq.nouns("four riders halted in a line across the trail on the bare rock.") == \
        ["the trail", "the bare rock"]
    assert sq.nouns("his hand against the black and the door jamb.") == ["the door jamb"]
    assert sq.nouns("Lucy at the table, the lamp warm, the narrow white collar of the dress.") == \
        ["the table", "the narrow white collar", "the dress"]
    assert sq.nouns("Close on Ferrier, the deep-set eyes hard, the faint pale line of the window.") == \
        ["the window"]


def test_the_alternate_falls_back_to_the_next_noun_phrase():
    riders = seg(0, size="wide", faces=[], frame="Wide of the trail: four riders in a line across the trail, "
                                                 "rifles across the saddles.")
    assert sq._thing(riders) == "the saddles"
    hand = seg(17, size="insert", faces=["brigham_young"],
               frame="Insert on his raised hand against the black of the door jamb.")
    assert sq._thing(hand) == "the door jamb"


# ---- D5  an alternate twin is reported and buys no retry ------------------------

def _cells(tmp_path):
    a = Image.radial_gradient("L").resize((90, 90)).convert("RGB")
    b = Image.linear_gradient("L").resize((90, 90)).convert("RGB")
    paths = []
    for k, im in enumerate((a, a, b)):
        p = tmp_path / f"c{k}.png"
        im.save(p)
        paths.append(p)
    return paths


def test_an_alternate_that_copies_its_base_is_an_advisory_pair_not_a_duplicate(tmp_path):
    paths = _cells(tmp_path)
    segs = [{"shot": 26, "sub": 0, "end": False}, {"shot": 26, "sub": 0, "end": False, "alt": True},
            {"shot": 27, "sub": 0, "end": False}]
    assert sq.duplicates(paths, segs) == []
    assert sq.alt_duplicates(paths, segs) == [("Q26_0", "Q26_0A")]


def test_two_base_cells_that_match_are_still_a_hard_duplicate(tmp_path):
    paths = _cells(tmp_path)
    segs = [{"shot": 26, "sub": 0, "end": False}, {"shot": 27, "sub": 0, "end": False},
            {"shot": 28, "sub": 0, "end": False, "alt": True}]
    assert sq.duplicates(paths, segs) == [("Q26_0", "Q27_0")]
    assert sq.alt_duplicates(paths, segs) == []
