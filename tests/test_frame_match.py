from PIL import Image, ImageDraw

from studio import frame_match as fm


def picture(seed_shape):
    im = Image.new("RGB", (768, 1344), "black")
    d = ImageDraw.Draw(im)
    if seed_shape == "face":
        d.ellipse((200, 200, 568, 700), fill="white")
    else:
        d.rectangle((100, 900, 668, 1300), fill="white")
    return im


def test_a_frame_is_matched_to_the_cell_it_resembles():
    cells = {"face": picture("face"), "backs": picture("backs")}
    assert fm.closest(picture("face"), cells)[0] == "face"
    assert fm.closest(picture("backs"), cells)[0] == "backs"


def test_identical_images_score_one():
    assert abs(fm.similarity(picture("face"), picture("face")) - 1.0) < 1e-6
