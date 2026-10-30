"""A 'half-moon fanlight' is a door, not the night (Jekyll ep06 T00, 2026-10-29).

Shot 0's day setup describes "a half-moon fanlight above it"; once the take went refs-only its prompt carried the
setup's place words and L33 refused it: 'a day take says moon'.  The night vocabulary (house_style.NIGHT, read by
time_of and L33) no longer reads 'moon' after 'half'."""
from studio import house_style


def test_a_half_moon_fanlight_is_no_night_word():
    assert not house_style.NIGHT.search("a brass knocker and a half-moon fanlight above it")
    assert not house_style.NIGHT.search("the half moon window over the door")


def test_the_moon_is_still_the_night():
    for said in ("the moon rides over the roofs", "moonlight on the cobbles", "a moonlit road", "moonrise"):
        assert house_style.NIGHT.search(said), said
