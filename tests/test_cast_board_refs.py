"""The storyboard drawer is told there are TWO pictures of each person, and
which wardrobe state this setup is in."""
from studio import episode_board as board
from studio.episode_spec import Shot

PHYSICAL = {"john_watson": "A lean man.", "stamford": "A stout man."}
WARDROBE = {"john_watson": "is bare-headed and carries the brown bowler in his left hand",
            "stamford": "is bare-headed and carries the black bowler in his left hand"}


def shots(n):
    return [Shot(index=i, section="friction", setup="lab", size="wide",
                 frame=f"frame {i}", motion="m") for i in range(n)]


class TestOneImagePerPictureNotOnePerPerson:
    def test_without_cards_the_drawer_is_told_what_it_has_always_been_told(self):
        said = board.describe_refs(["john_watson"], PHYSICAL, previous=False)
        assert "Image 2 is John Watson: A lean man." in said
        assert "Image 3" not in said

    def test_with_cards_the_face_and_the_clothes_are_two_separate_images(self):
        said = board.describe_refs(["john_watson"], PHYSICAL, previous=False, wardrobe=WARDROBE)
        assert "Image 2 is John Watson, his face and hair: A lean man." in said
        assert "Image 3 is John Watson's clothes, hands and things: in this scene he " \
               "is bare-headed and carries the brown bowler in his left hand." in said

    def test_the_previous_sheet_keeps_its_place_at_the_end_of_the_list(self):
        said = board.describe_refs(["john_watson", "stamford"], PHYSICAL,
                                   previous=True, wardrobe=WARDROBE)
        assert "Image 6 is the previous storyboard sheet" in said

    def test_the_state_sentence_reaches_the_sheet_prompt(self):
        said = board.prompt(shots(3), "a lab", ["john_watson"], PHYSICAL,
                            previous=False, wardrobe=WARDROBE)
        assert "his face and hair" in said and "clothes, hands and things" in said

    def test_a_single_panel_redraw_carries_the_same_two_pictures(self):
        said = board.panel_prompt(shots(1)[0], "a lab", ["john_watson"], PHYSICAL,
                                  wardrobe=WARDROBE)
        assert "Image 3 is John Watson's clothes, hands and things" in said
