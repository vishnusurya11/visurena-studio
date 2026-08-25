Higgsfield uses cookies. Essential cookies keep the site working. Others let us measure how the site is used, improve it, and see which campaigns bring people here — some of these are set by third-party partners. Under some US state privacy laws, this use of third-party cookies may count as a sale or sharing of personal information. You can opt out at any time

Cookie Notice
Do Not Sell or Share My Personal Information
Dismiss
Cookie Preferences

Sign up and get additional discount on Premium plans
Extra discount


Supercomputer

Login
Sign up
Community
/
Red Flag
Community
/
Red Flag


1×


0:00 / 2:16



Red Flag
19 990 views
·
5 days ago
higgsfield.studio
A pitch-black Hong Kong neo-noir about romance, betrayal and, above all, self-defense. A woman is home alone, still deciding whether her new boyfriend is worth keeping, when a burglar breaks into her flat after midnight: the "burglar" turns out to be the boyfriend, Li, letting himself in with a surprise bouquet - the reddest flag of all. What Li doesn't know is that she's a quiet martial-arts champion... and she's just made up her mind.


Any story. Any genre. One prize pool.

$1,000,000

Assets












































































image generation









































image generation

Project brief

Logline: One rainy night in 1990s Hong Kong, a woman walks home still deciding whether her new boyfriend deserves a yes. After midnight, someone picks the lock of her tiger-painted door. The "burglar" is the boyfriend himself — Li, sneaking in with a bouquet to surprise the woman he loves. It's the reddest flag of all. What Li never knew: she's a martial-arts champion. And she's just made up her mind.


16x9 (2).png


About the project
RED FLAG is a ~2-minute photoreal AI short film — a pitch-black Hong Kong neo-noir about romance, betrayal and, above all, self-defense. Every frame is generated: no sets, no cameras, no filmed footage. Format: 1.85:1, Cantonese, minimal dialogue.

The film lives in one flat on one rainy night, and its two hardest jobs were decided by the material itself: holding a strict '90s film-noir look across every shot, and landing a real fight — a three-move takedown that AI video models break by default. Most of this breakdown is about those two battles, and about the geometry in between: doors, stairs, corridors and a bead curtain that all had to stay put.

The tools
Seedance 2.5 — every video shot.
Higgsfield Soul Cinema — character sheets.
Seedream 5.0 — image edits


Canvas preview

Higgsfield Canvas


01 · PRE-PRODUCTION

Assets
An asset is a pair: text + image. The text descriptor goes into every prompt word for word; the image anchors the model. Our registry grew to ~30 tagged assets: two leads and a grandmother, the tiger door, the half-open peony bouquet, a brass key with a tiger charm, a red brocade handbag, four grocery bags, corridors, a stairwell, a kitchen, the night skyline — plus a separate shelf of staging diagrams. Every prompt calls them by @tag, never "the man" or "the door."

One detail did heavy lifting: Li's descriptor pins his silhouette (olive pinstripe '90s suit, burgundy shirt, gold chain), because for half the film his face is never shown — the burglar has to be recognizable from the back.



@char_RF_woman_ver.png




02 · PRE-PRODUCTION

The film is graded in the prompt, not in post
A style prefix is pasted into every single prompt:

Style: 1990s Hong Kong neon noir, shot the way films were shot in the '90s.
Arriflex 35 III, Zeiss Super Speed primes, spherical 1.85:1.
Fuji Eterna 500T processed cool — coarse organic grain, halation on
practical lights, shallow focus. Low-light night, crushed and moody.
We tested the Kodak Vision3 500T first. Eterna won for one reason: its shadows drift green — and this film lives in green.

The color war: green vs yellow. Seedance 2.5 kept flipping our cold teal corridors into warm yellow. The leak came from the references themselves — a lit window here, warm globe lamps there — and the model amplified it. Negative lists ("no yellow") did nothing. Positive form worked:

The dominant color must be cold teal-green. Yellow exists only inside
the lamp bulb and a palm-sized halo beneath it. If the frame turns
yellow, the frame is wrong.
When a reference photo had a glowing red window we couldn't crop out, we wrote: "That window glowing in the reference is switched off in our film." The model believed i

de346e18-59ea-4138-b10f-484172fed4bc.png




03 · PRODUCTION

A diagram decides the frame; a location decides the texture
Attach a location photo and the model takes it as the framing reference — camera, angle, everything. So we split the roles: a flat outline diagram (frontal or top-down, letters instead of people) locks geometry and camera; the location photo feeds only surfaces and light. The diagram is attached LAST, and the prompt says it out loud: "Composition and camera = the diagram, not the location photo." When the model still grabbed the wrong reference, we deleted that reference from the shot entirely. Fewer anchors beat better instructions.



tig-diagram.skill
SKIL


Screenshot 2026-08-19 at 18.50.38.png


The throw that flew into the wrong room. The film's key shot kept teleporting: Li would fly off into the hallway one take, out the window the next — wide shots locked onto the location reference's angle and dragged the action into its geography. We demoted locations to "place, set dressing and light," banned shots from sitting on the reference's axis, and nailed the world down with anchors: the camera looks only at the kitchen, red beads in the foreground, he flies headfirst through the beads.





04 · PRODUCTION

Physics you have to write down
Doors were our worst "actors". Hinge side, inward vs outward swing, the tiger painted only on the outer face — every shot repeats the full door geometry, because the model reinvents it every time. Scale needed a ruler in the text: "the railing is 110 cm; on a 185 cm man the top rail lands just above his belt"— otherwise the railing floated to his chest. Anatomy needed a headcount: after a third hand showed up picking a lock, every close-up carries "there are only two hands in the frame, both belonging to the same person, entering from the same sleeve."

We also had trouble keeping a window open — even within a single sequence. The heroine would open the window in one clip, but in the following shots the model could forget it was open, because the asset showed it closed and the model trusted the reference over the story. So we made a separate asset with the window open, and it made things dramatically easier — the continuity slips mostly disappeared.



Walking is the hardest stunt
The staircase entrance nearly broke us: the two women had to rise slowly out of the stairwell — heads first, then shoulders, then legs, lifted step by step by stairs the audience never sees. The model kept teleporting them up in one jump, or deleting the stair opening and bricking it into a solid wall. The shot only held after we wrote the rise as physics ("lifted into frame one invisible step at a time, over two to three seconds") and made the opening a named, mandatory object.

Ordinary walking needed its own lock — gliding, both feet airborne, the same foot stepping twice: "heel lands first, strict left-right alternation, one foot always on the ground." Keeping two people side by side took more: "shoulder to shoulder, on one depth line, both heads the same size," or the grandmother drifted ahead. And matching cuts exposed a sneaky one — camera speed. Two tracking shots of the same walk came out at different speeds ("fast feet, slow backs"), so the prompt now states the camera speed of shot 9 equals shot 10, exactly.





05 · PRODUCTION

A fight cannot be edited into smoothness
The finale is a three-move takedown. Generated as independent clips it came out choppy: each clip re-guessed pose and tempo, and pauses crept into every cut. Two things fixed it: frame-chaining (the last frame of clip N becomes the first frame of clip N+1, with the action crossing the cut mid-move), and for the money move — one continuous take, the whole combination written as a single timeline in seconds, real-time speed, slow motion banned by name — video models love to slow a fight down on their own.

The choreography itself was written like a fight coordinator's notes, not a mood. Style is characterization: her movements are soft, circular, chin-na redirects and push-hands — a champion spending minimum force; his are straight, heavy and late. Every move is named and vectored, because the model flips physics whenever it's left to guess: the throw is written as "she rolls him over herself with her foot; he lands face toward her, head toward the window" — without the vector, his body landed a different way every take.

Fight frames got their own blocking diagrams — stick-figure maps for the hands and the legs at each keyframe, attached as first-frame geometry. And when full-body continuity was too expensive to hold, we cut into the body: quick inserts of hands, waist, feet — jump cuts hide transitions, add impact, and a close-up of feet is far harder to break than a wide shot of two bodies. One camera move did the most work: a single shot rising from her feet upward, and mid-rise she sweeps him off his.




Comments44

Write a comment...





profile picture of @hallcyonn
hallcyonn
1h
omg🔥

Reply
profile picture of @mccarthylobster1699
mccarthylobster1699
7h
cant wait for 3.0

Reply
profile picture of @loadingcartoons
loadingcartoons
8h
He shouldn't knocked first. Tehehe

Reply
profile picture of @descartesaxolotl1537
descartesaxolotl1537
9h
AMAZING

Reply
profile picture of @pythagorasquokka1504
pythagorasquokka1504
1d
This is so cool

Reply
profile picture of @gibberstudios
gibberstudios
1d
nice work

Reply
profile picture of @noorvisuals
noorvisuals
1d
great work!

Reply
profile picture of @rothkocarrot1849
rothkocarrot1849
1d
I love it

Reply
profile picture of @shiningswan1395
shiningswan1395
1d
Just wondering how many credits are spent to create this 2 minutes video?

Reply
profile picture of @cookingwallaby139
cookingwallaby139
1d
wow really nice

Reply
profile picture of @cauchyferret1678
cauchyferret1678
1d
This is so awesome!!!! So cool, good luck!

Reply
profile picture of @jammingotter1362
jammingotter1362
1d
Thatt's crazy work

Reply
profile picture of @evolvingtadpole1436
evolvingtadpole1436
1d
wow its amagzing

Reply
profile picture of @wizard_337
wizard_337
2d
YOOOO! HIGGS LET ME GET ON THE MOVIE SQUAD I MAKE TOP NOTCH MOVIES TOO!! CHECK MY YOUTUBE I JUST STYARTED ITS ALREADY GETTING HUNDREDS OF THOUSANDS OF VIEWS!

Reply
profile picture of @streamingbroccoli_vip
streamingbroccoli_vip
2d
Would this qualify for the Global Film Festival being that it's under 3 minutes?
1
Reply
profile picture of @playfulstar1673
playfulstar1673
3d
图片一键卸载甲视频生成器。全网唯一一款最牛最强大的AI工具！无违禁词限制，怎么想怎么输入提示词指令即可自动生成你想要的图片或视频。可随意发挥你的想象！😍😍懂的都懂😍😍支持手机电脑，操作简单，生成快，效果超赞！适合做短视频、创意剪辑、生活记录等，功能强大，软件付费下载后可永久免费消费无限制！补充充值无二次！私信代做看效果！有需要朋友的赶紧下载，有问题随时私聊，包商店，包售后！官网地址 htt❓ps://❓698fd1a391e0d❓.site123❓.me 售后电报群 htt❓ps:/❓/t.❓me/+pF❓_6XFCh❓BX5jN2Yx （去掉问号❓可访问！）

Reply
profile picture of @abramoviccake1609
abramoviccake1609
3d
Amazing wow

Reply
profile picture of @kusamacheese1807
kusamacheese1807
3d
Amazing 😍 so beautiful

Reply
profile picture of @julienn_mitric
julienn_mitric
3d
Mi-a plăcut, in mod deosebit finalul :D

Reply
profile picture of @mondrianwaffle1796
mondrianwaffle1796
3d
Amazing and beautiful
1
Reply
profile picture of @yuruying
yuruying
3d
cool

Reply
profile picture of @pulsing_table_42
pulsing_table_42
4d
Amazing!

Reply
profile picture of @impressionistruby1493
impressionistruby1493
4d
Amazing!

Reply
profile picture of @reptuyou
reptuyou
4d
Very good tecnical control

Reply
profile picture of @prefab_beluga_1007
prefab_beluga_1007
4d
hhhhhhhhhhhhhhhhhhhhhhhhhhh i love it

Reply
profile picture of @hanadi
hanadi
4d
Best of luck

Reply
profile picture of @hanadi
hanadi
4d
Good luck 👍

Reply
profile picture of @neoclassicallamp1013
neoclassicallamp1013
4d
awesome

Reply
profile picture of @industrialbutterfly1426
industrialbutterfly1426
4d
Support Cantonese. 🎉🎉🎉

Reply
profile picture of @cinematicblueberry1513
cinematicblueberry1513
4d
So realistic

Reply
profile picture of @now_1020
now_1020
4d
Very dramatic and entertaining.

Reply
profile picture of @birdbrains
birdbrains
5d
Peak af

Reply
profile picture of @van_goghcupcake1838
van_goghcupcake1838
5d
황정민 ㅎㅎㅎㅎ
1
Reply
profile picture of @dali_broccoli_1018
dali_broccoli_1018
5d
🇨🇮🇨🇮🇨🇮

Reply
profile picture of @synthwavebroccoli1362
synthwavebroccoli1362
5d
the style and production is too good

do watch my film too its SYNARA

Reply
profile picture of @postmodernwombat1412
postmodernwombat1412
5d
amazing promopts

Reply
profile picture of @prabowo
prabowo
5d
amazing one

Reply
profile picture of @commercialwhale1486
commercialwhale1486
5d
amazing

Reply
Show 1 reply
profile picture of @nickharborne
nickharborne
5d
Very cool to see others work flows. Great learning perspective here. AND GREAT VIDEO!

Reply
profile picture of @dijkstrakangaroo1248
dijkstrakangaroo1248
5d
i see there are too many fail generations in assets, like lock picking, they waste too many credits their self

Reply
Information

Views
19 990
Generations
3 524
Created time
August 19, 02:21
Powered by

Frames and Scenes

Cinema Studio

Recommended

Dusk
Dusk
Higgsfield Soul
If you stop loving me, I'll die — I don't like dying, but for our love I'm ready to go that far
If you stop loving me, I'll die — I don't like dying, but for our love I'm ready to go that far
Higgsfield Studio
MAY ALL YOUR PROBLEMS DISAPPEAR
MAY ALL YOUR PROBLEMS DISAPPEAR
folkjuice1589
Shiftnex
Shiftnex
geometrictoaster1631
SEEDANCE 2.5 PROMPT TESTING
SEEDANCE 2.5 PROMPT TESTING
thomas_lundstrom
The Chrononauts
The Chrononauts
staticshok
Chloe花火大会
Chloe花火大会
shthfu
The Wild Return
The Wild Return
maxhuettl
Ziak Edit
Ziak Edit
antoine_malvezin
Nike X PeakyBlinders
Nike X PeakyBlinders
jamil_safari
TWO HEARTBEATS
TWO HEARTBEATS
jawidiqbalanwar
INK SMOKE ART
INK SMOKE ART
jaganathan_nair
New project
New project
vintagesoda1379
Wonderful World
Wonderful World
actionlaki
Unleash The Venum
Unleash The Venum
antoine_malvezin
Lashful - Eyelash Growth Serum
Lashful - Eyelash Growth Serum
helluvacast
imagine that daily
imagine that daily
disfaus
GOOD BAD DEATH
GOOD BAD DEATH
roozafzoun
Shommy and MIra
Shommy and MIra
shommy
The Promise
The Promise
dalyai