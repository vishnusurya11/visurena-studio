# Getting a 2K master from MiniMax-H3 anime takes without changing the style

Research date: 2026-11-02. Read-only web research. Nothing was run, installed or downloaded.
Labels: TESTED = someone published numbers or a side-by-side. CLAIMED = a vendor, paper or forum post says so, with no measurement we can check. UNKNOWN = nothing found.

## The problem
The official H3 2K regenerate pass re-draws the picture. It is built for photoreal footage. A 1344x768 anime take comes back sharper, but with texture, grain and a darker palette. The look changes.

## 1. What the official Open-H3-Regenerate-2K is
Sources: Hugging Face model card and ComfyUI Wiki, 2026-10-27.
- A 3D-conv latent upscaler enlarges the encoded draft latent. No pixel resize, no re-encode. (CLAIMED by NVIDIA)
- Start state = (1 - 0.909375) x upscaled + 0.909375 x noise. Three Euler steps on sigmas 0.909375, 0.857143, 0.666667, 0. CFG 1. (stated on the card)
- One merged LoRA, rank 576: refiner (rank 384) + LightX2V FL2VA Turbo v1.2 (rank 128) + LMS Sharp v1.0 (rank 64). Sharp also has 50 separate "curve" AdaLN branches (FP32, 1.24 GB).
- A fast 24-layer non-causal VAE decoder: 1.6 s versus about 15 s for the released VAE on a 2560x1440 clip.
- Timing on one B200, 5 s clip: 87 s standard, 22 s with NVIDIA's own engine and fast decoder. No 4090 number exists. (NVIDIA's own measurement)
- Preference study: 200 blinded judgments, open refiner preferred in 87%. (NVIDIA's own, photoreal-oriented)
- No official ComfyUI nodes. No statement about anime or stylised input. No denoise guidance for keeping the input look. The card says the bundle is "not covered by a single blanket license".

A start sigma of 0.909 is almost a full redraw. So the official recipe itself is not a light touch.

## 2. Is it usable in ComfyUI?
| Piece | Status | Source type |
|---|---|---|
| Refiner LoRA alone (rank 384) | Published by Kijai, for pairing with other distills | CLAIMED (wiki) |
| Merged LoRA + curve branches | Community node: 1038lab ComfyUI-Open-H3-Regenerate-2K (GPL-3.0). Full BF16 LoRA 8.8 GB, r128 LoRA 1.95 GB ("low VRAM"), curve branches 1.24 GB. Its page lists the same sigmas, euler, CFG 1. The NVIDIA team said on the model page that this node is not theirs. | Unofficial |
| Fast VAE decoder | No ComfyUI-ready file found | UNKNOWN |
| Latent upscaler | Tr1dae ComfyUI-MiniMaxH3_LatentUpscaler (about 147 stars, no releases). The repo wiki says it is not a learned upscaler. A ComfyUI Wiki news item says a trained 2x model exists. The sources disagree. | Mixed |
| Wiki warning | A straight LoRA conversion gives wrong weights unless a SwiGLU transform is applied. | CLAIMED (wiki) |

## 3. What the community reports
- Tr1dae wiki: for the second pass, start sigma about 0.25-0.45. "Too little can't hide the upsample, too much rewrites the clip." Use euler or res_multistep, non-ancestral. Audio denoise 0. No anime notes, no timings. (CLAIMED guidance, no numbers)
- aistudynow guide: first pass 0.5 MP, second 1.5-2 MP. 1.5 vs 2 MP differed little. A 0.2 MP first pass lost detail and turned a two-person reference into three people. No timings, no anime. (TESTED by one author, qualitative)
- HF discussion #7 on the Regenerate card: the 3-step refine removes subtle motion (blinks, a yawn, water). The reporter saw it mostly kept on a Flex fl2va base. Not a single-variable test. (one report)
- Community claim: 10 s of 1344x768 in 150-180 s with a speed node and a Turbo LoRA; 0.5 MP to 1080p in under 5 min on a 3090. About the latent-upscale route. Unverified.
- No public report of the refiner on anime footage was found. No 4090 timing for the refiner was found.

## 4. Style-preserving techniques (general)
| Technique | Evidence |
|---|---|
| Lower start sigma | Tr1dae wiki says 0.25-0.45. No published anime test. |
| Latent upscale, not pixel upscale then encode | Official design. A smooth lanczos image gives the LoRA nothing to keep, so it may invent texture (our reasoning, not tested elsewhere). |
| Wavelet colour fix | StableSR extension and many VSR repos: keep the low frequencies (colour, shading) from the source, take the high-frequency detail from the output. The README says AdaIN (global mean/std) is often not enough and wavelet suits uneven shifts. Anecdotal. Per frame; no video-specific study found. |
| SeedVR2 colour options | lab (recommended for fidelity), wavelet, wavelet_adaptive, hsv, adain, none (ComfyUI node README). |
| Non-ancestral sampler | Tr1dae wiki. Our sa_solver run was stochastic. |
| Reference or style-image conditioning | Nothing found that shows it keeps style for this model. |
| Temporal consistency | SeedVR2: overlap batches; low batch size can flicker (extension guide). |

## 5. Alternatives
| Method | Style evidence | Speed evidence | Licence (commercial use) |
|---|---|---|---|
| NVIDIA RTX VSR | A 4090 user said it looks nearly identical to the original (forum, anecdotal). Adds little detail. | Real time | NVIDIA SDK terms. Not checked. |
| SeedVR2 (3B/7B) | A competing vendor's blog says flat fills stay clean (CLAIMED). ComfyUI docs call it conservative. A guide advises pre_downscale 0.5 for low-res anime. No independent anime test. | ComfyUI docs: 312 s for a 10 s 720p clip to 1080p on an RTX 5090. Topaz forum: about 1 fps, hardware unknown. 24 GB fits 3B FP16; block swap and tiled VAE for 7B. | Apache 2.0 |
| FlashVSR v1.1 | No anime test. A "more conservative than SeedVR2" claim from web comparisons. | ComfyUI docs: 41 s for a 10 s 720p clip to 1080p on a 5090. Repo: 17 fps at 768x1408 on A100. Needs Block-Sparse Attention; 40-series support is "unknown" per the authors. Built mainly for 4x. | Apache 2.0 |
| STAR | None for anime | 39 GB VRAM for a 72-frame 426x240 clip at defaults; 24 GB suggested minimum | MIT (I2VGen-based) or CogVideoX licence |
| Upscale-A-Video | None | Not stated | NTU S-Lab License 1.0. Text not read. Treat as non-commercial until checked. |
| VEnhancer | None | Single GPU needs an A100 80 GB | README names no licence. Check LICENSE. |
| DOVE | None | One step, "up to 28x faster" than MGLD-VSR. Inference VRAM not stated. | Apache 2.0 repo; base is CogVideoX, so weights may carry its licence |
| APISR | Anime-made, image-based, per frame. No temporal metric in the paper. | Not measured here | Not verified |
| AnimeSR | Anime-trained video model | Not measured here | Not verified |

## 6. Recommended tests
1. Low-start-sigma regenerate on the latent route, then a wavelet low-frequency swap. Sigmas about 0.45, 0.3, 0.15, 0 (or 0.6, 0.45, 0.25, 0), euler, refiner 0.7 plus Turbo 0.75, CFG 1. Then keep the source colour and shading and take only the regen's high frequencies. Estimated 8-14 min per 7 s (estimate, not measured).
2. SeedVR2 3B, 2x, lab colour fix, temporal overlap 4-8, tiled VAE, lowest strength. Estimated 5-15 min per 7 s (estimate from the 5090 figure).
3. FlashVSR v1.1, 2x. Estimated 1-4 min per 7 s (estimate), if its attention backend runs on a 4090.
Controls for all: lanczos 2x and RTX VSR 2x.

Pass criteria, same crops, same shot: luma edge energy within 1.15x of the source; mean RGB within 3%; line width within 15%; faces unchanged by eye; no added wall grain; no new flicker over 7 s. Better additions: a low-pass (blur sigma about 4 px) difference to the source under 2% of range, which proves the shading is kept; frame-to-frame edge-energy variance no higher than the source; and a blink/motion check (HF discussion #7).

## 7. Biggest uncertainties
- No one has published a test of the 2K refiner on anime. Every anime claim for every method here is unmeasured.
- Whether the Turbo and Sharp parts inside the merged LoRA, not the start sigma, cause the texture. Only separate tests can say.
- No 4090 timing exists for the refiner, SeedVR2 or FlashVSR. All times above are estimates.
- Licence: the MiniMax H3 Community License lists an "Applicable Territory" of worldwide except the EU, UK, Korea and the US. Ask an attorney. This is not legal advice.

## Sources
- https://huggingface.co/Efficient-Large-Model/Open-H3-Regenerate-2K (read 2026-11-02)
- https://huggingface.co/Efficient-Large-Model/Open-H3-Regenerate-2K/discussions/7
- https://huggingface.co/Efficient-Large-Model/Open-H3-Regenerate-2K/discussions/1
- https://comfyui-wiki.com/en/news/2026-10-27-open-h3-regenerate-2k
- https://comfy.icu/extension/1038lab__ComfyUI-Open-H3-Regenerate-2K
- https://huggingface.co/Kijai/MiniMax-H3_comfy
- https://github.com/Tr1dae/ComfyUI-MiniMaxH3_LatentUpscaler/wiki
- https://comfyui-wiki.com/en/news/2026-08-17-minimax-h3-trained-latent-upscaler
- https://aistudynow.com/how-to-upscale-minimax-h3-to-2k-in-comfyui/
- https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE
- https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler
- https://github.com/IceClear/SeedVR2
- https://github.com/OpenImagingLab/FlashVSR
- https://docs.comfy.org/tutorials/utility/video-upscale
- https://community.topazlabs.com/t/sls-vs-slm-vs-seedvr2-vs-flashvsr-comparison/98005/1
- https://upsampler.com/blog/seedvr2-diffusion-upscaler
- https://github.com/NJU-PCALab/STAR
- https://github.com/sczhou/Upscale-A-Video
- https://github.com/Vchitect/VEnhancer
- https://github.com/zhengchen1999/DOVE
- https://arxiv.org/pdf/2403.01598 (APISR)
- https://huggingface.co/toto10/extensions/blob/refs%2Fpr%2F6/sd-webui-stablesr/README.md (wavelet colour fix)
- https://comfy.icu/node/STARVSR_ColorFix

## Measured result (2026-11-02)

We rebuilt NVIDIA's official stack from its three parts (refiner, FL2V Turbo v1.2, LMS sharp, all at 1.0; euler;
explicit sigmas; no shift) and ran it on a 7.3 s anime take on one RTX 4090 at 2560x1440.

| Version | Time per 7 s | Edge energy vs source | Low-band shift |
|---|---|---|---|
| RTX VSR 2x | about 1 min | 1.37x | 0.27% |
| Official sigmas 0.909 / 0.857 / 0.667 | 945 s | 2.17x | 1.29% |
| Light sigmas 0.6 / 0.45 / 0.25 | 653 s | 1.11x | 0.57% |
| Lightest sigmas 0.45 / 0.3 / 0.15 | 660 s | 1.02x | 0.56% |
| Light + source low band | +CPU | 1.12x | 0.27% |

![Raw, RTX 2x, official regen, light regen with the source low band](T08_closeup.jpg)

The official recipe repaints anime. Painted stone becomes photo-real grit, skin gets etched lines, and a coat turns
into strands. Light settings keep the drawing but add no more detail than RTX VSR 2x, at about ten times the time.
On stylised footage, RTX VSR 2x remains the better 2K step.

A relative mean-RGB check fails dark scenes (a one-level shift reads as 4%); use an absolute low-band difference.

**SeedVR2 3B** (rank 2 in the research) did not finish one 7.3 s shot within a 60-minute cap at 1440p on the
same RTX 4090: 24 GB of VRAM full, the GPU memory-bound at about 100 W. On this hardware it is not a practical
2K step for a 20-shot scene.
