# Quest 3 Touch Plus haptics: hardware, PC OpenXR APIs, and design craft for stick-and-puck feel

Scope: what the Quest 3 Touch Plus controllers can output, how to drive them from a Python/pyopenxr PC app over Link, and evidence-based ways to design impact, scrape, texture and "weight" vibrations. Controllers in hand only (no props, vests, gloves). Researched 2026-11-07.

Two findings were checked directly on Jon's PC rather than taken from the web:
- **Extensions on his runtime:** his Meta PC runtime (reports "Oculus" 1.208.0) exposes `XR_EXT_haptic_parametric`, `XR_FB_haptic_pcm` and `XR_FB_haptic_amplitude_envelope`, each at revision 1. It also exposes `XR_META_touch_controller_plus`, `XR_FB_touch_controller_pro` and `XR_FB_touch_controller_proximity`.
- **pyopenxr bindings:** the installed pyopenxr (1.1.6501, in `C:\dev\vr-hockey\spike0\.venv`) already wraps all three haptic extensions.

These checks are marked "local check" below. Everything else is cited to its source.

---

## 1. Hardware: what actuator is in the Touch Plus, its range, and how it compares with Quest 2 and Touch Pro

### Takeaway
Each Touch Plus controller has one wideband voice-coil motor (VCM) in the grip, which drives the palm. Meta says it can play frequencies "up to 500 Hz", and that it matches Touch Pro "with slightly lower output intensity", without Touch Pro's extra thumb and trigger actuators. The Quest 2 controllers (Touch) instead use a narrowband LRA at one fixed frequency. The only measurement found: 2.62 G peak-to-peak at 120 Hz and full amplitude. No public teardown of the Touch Plus was found.

### Cited Findings
- **Touch Plus actuator (Meta, PC native docs):** "Touch Plus controllers have one haptic actuator in the body of the controller. This actuator is a VCM (Voice Coil Motor) that provides wideband feedback to the palm of the user." It does not support localized haptics like the Touch Pro. — [Meta: Touch Plus controllers (PC native)](https://developers.meta.com/horizon/documentation/native/pc/native-touch-plus-controllers)
- **Meta's comparison table:**
  - Meta Quest Touch: narrowband LRA, "Single frequency with amplitude control, simple signals".
  - Touch Pro: wideband VCM, "Frequency and amplitude control: sharp and precise clicks, complex signals".
  - Touch Plus: wideband VCM, "Same as Touch Pro with slightly lower output intensity".
  - VCMs enable "operation across a range of frequencies up to 500 Hz". No lower bound or resonant frequency is published.
  - [Meta: Haptics technology](https://developers.meta.com/horizon/design/haptics-technology/)
- **API behaviour by controller (native docs):**
  - Touch Pro, Touch Plus and later have a VCM. Frequency points and varying frequency are supported, and PCM "directly drives the haptic motor".
  - Meta Quest Touch and earlier (the Quest 2 controllers) have an LRA. Frequency points are ignored, the motor vibrates at a fixed frequency, and PCM plays "an equivalent haptic effect".
  - Touch Pro localized haptics: one VCM plus two LRAs (thumb and trigger). The LRAs take simple haptics only, at a fixed frequency.
  - [Meta: OpenXR haptic feedback](https://developers.meta.com/horizon/documentation/native/android/mobile-openxr-haptic/)
- **Touch Pro works with Quest 3:** Touch Pro controllers are compatible with Quest 3, and Touch Plus was presented as sharing the "TruTouch haptics" branding. This is press coverage from 2023, not a spec sheet. — [Road to VR (2023)](https://roadtovr.com/quest-3-launching-new-controllers-will-also-support-touch-pro/)
- **Single motor, not several:** some press and retail copy describes "TruTouch haptic motors spread throughout the controller". This conflicts with Meta's developer docs, which state one actuator. Trust the developer docs. — [Meta: Touch Plus (PC native)](https://developers.meta.com/horizon/documentation/native/pc/native-touch-plus-controllers)
- **Measured output (Sabnis et al., CHI 2026):** they used Quest 3 controllers with an IMU strapped on, at 120 Hz. Peak-to-peak acceleration was 2.62 ± 0.24 G at amplitude 1.0, 1.83 ± 0.17 G at 0.7, and 1.07 ± 0.12 G at 0.4. In other words, output is roughly linear in commanded amplitude at that frequency. — [Sabnis et al., "Connected Material Experiences using Bimanual Vibrotactile Crosstalk in VR", CHI '26 (preprint)](https://umtl.cs.uni-saarland.de/paper_preprints/sabnis-et-al-bimanual-haptics-pre-print-chi-2026.pdf)
- **Same paper on the actuator type:** it describes the Quest 3 controller actuators as voice coil actuators with "a wide-band frequency response up to 500Hz" and a "stable amplitude response across a broad range of frequencies", as opposed to LRAs tuned to one resonance. — [Sabnis et al. CHI '26](https://umtl.cs.uni-saarland.de/paper_preprints/sabnis-et-al-bimanual-haptics-pre-print-chi-2026.pdf)
- **Studio effects by controller:** custom effects from Meta Haptics Studio "work best on Meta Quest Pro, Meta Quest 3 and up" and are backward compatible with Quest 2. — [Meta: Haptics system / Studio docs](https://developers.meta.com/horizon/design/haptics-system/)
- **Teardowns:** the only iFixit teardown found is the original 2016 Oculus Touch. Its haptic motor was a moving-mass voice-coil-type actuator, glued in. iFixit's Switch teardown called the Switch's LRA "nearly identical" to the Touch motor. No Touch Plus teardown was found. — [iFixit: Oculus Touch teardown](https://www.ifixit.com/Guide/Oculus+Touch+Teardown/75109)

### Inferences
- **Frequency control is real.** The Touch Plus is the first stock Quest controller where frequency is a design variable, so a soft rubber thud and a hard click can differ in spectrum, not just in strength. Quest 2-era advice ("only amplitude and duration matter") no longer applies.
- **Strength is modest.** About 2.6 G peak-to-peak at full drive is useful, but nowhere near the acceleration spike of a real puck hitting a stick. Contrast and timing will matter more than absolute strength.
- **Optional upgrade within the rule:** Touch Pro controllers are still "controllers in hand". Their thumb and trigger LRAs could add a second, localized channel, for example a sharp click at the index finger. That is an option, not a requirement.

### Gaps
- **No published frequency response.** There is no curve or resonance figure for the Touch Plus VCM, and no lower bound below 500 Hz. API constants such as the parametric 1-1000 Hz limits are not device specs. Jon could measure it himself with a phone accelerometer app or a cheap IMU, as Sabnis et al. did.
- **No teardown or part number** was found for the Touch Plus actuator.
- **No data on output across frequency.** The only measurement is at 120 Hz. How hard it shakes at 50 Hz or 300 Hz is unknown.

---

## 2. APIs over PC Link: extensions, sample rates, buffers, latency, and the Meta Haptics SDK and Studio

### Takeaway
On Jon's own runtime (Meta PC, 1.208.0), all three high-fidelity paths are exposed: `XR_FB_haptic_pcm` (raw waveform), `XR_FB_haptic_amplitude_envelope`, and the new cross-vendor `XR_EXT_haptic_parametric` (amplitude and frequency curves plus transients). pyopenxr 1.1.6501 already wraps them. The `frequency` field in the simple `XrHapticVibration` call is ignored on Meta, so his current code cannot vary pitch. The best direct path from Python is PCM, synthesized at the controller's own sample rate and streamed with `append`. One measurement over Link put motion-to-vibration latency at about 21.5 ms.

### Cited Findings
**Extension availability**
- **Local check on Jon's PC:** the installed runtime manifest is "Oculus OpenXR" (`C:\Program Files\Meta Horizon\Support\oculus-runtime\oculus_openxr_64.json`). `xrEnumerateInstanceExtensionProperties` lists `XR_EXT_haptic_parametric` rev 1, `XR_FB_haptic_amplitude_envelope` rev 1 and `XR_FB_haptic_pcm` rev 1, plus `XR_META_touch_controller_plus`. Instance properties report runtime "Oculus" 1.208.0. (This shows the extensions exist on PC; it does not prove the behaviour on Touch Plus over Link.)
- **Khronos inventory:** the OpenXR Inventory lists "Meta (PC)" as supporting `XR_FB_haptic_pcm` and `XR_FB_haptic_amplitude_envelope`, and does **not** list `XR_EXT_haptic_parametric`. That snapshot is older than runtime 1.208; the local check shows parametric is now present. SteamVR (Windows, Linux, Steam Frame) supports none of the three. — [Khronos OpenXR Inventory: runtime extension support](https://github.khronos.org/OpenXR-Inventory/runtime_extension_support.html)
- **`XR_EXT_haptic_parametric` origin:** it is a multi-vendor extension, added in OpenXR spec 1.1.60 (2026-05-20), registered as extension number 776, revision 1, and "Not ratified". It describes amplitude and frequency points as (time in ns, value) pairs plus transients, with longer effects streamed as first, intermediate and last frames through repeated `xrApplyHapticFeedback` calls. — [Khronos: XR_EXT_haptic_parametric](https://registry.khronos.org/OpenXR/specs/1.1/man/html/XR_EXT_haptic_parametric.html); [OpenXR-Registry release 1.1.60](https://github.com/KhronosGroup/OpenXR-Registry/releases/tag/release-1.1.60)

**What Meta's docs say about each path**
- **Simple haptics:** "`XrHapticVibration::frequency`: Ignored. Changing vibration frequency with the simple API is not supported."
- **Parametric:** Meta recommends parametric haptics for most cases (easy to use, wider runtime support, device-agnostic data).
  - Amplitude, frequency and transient values run 0.0-1.0, and frequency 0-1 is "automatically mapped to the controller's full supported range".
  - Absolute frequency can be set with `minFrequencyHz` and `maxFrequencyHz` in the first frame; `XR_FREQUENCY_UNSPECIFIED` means the controller's full range.
  - The first amplitude point must be at 0 ns.
  - Streaming needs at least 2 amplitude points in the first frame and at least 1 per later frame. `xrHapticParametricGetPropertiesEXT()` returns `minimumFirstFrameDuration` and `idealFrameSubmissionRate`.
- **PCM:** PCM drives the VCM directly. The example uses a 2000 Hz source sample rate and a 120 Hz sine; the runtime resamples to the controller's rate. Query that rate with `xrGetDeviceSampleRateFB()`, which returns 0 if PCM is unsupported and can change when the controller changes.
- **Amplitude envelope:** takes a duration in ns and an amplitude array.
- **Known Meta bug:** triggering thumb LRA haptics on both hands with `XR_PATH_NULL` makes the right thumb play for double the time. This is Touch Pro only.
- [Meta: OpenXR haptic feedback (native)](https://developers.meta.com/horizon/documentation/native/android/mobile-openxr-haptic/)
- Note: this page lives under the Android native docs. Assuming the same behaviour on the PC runtime is an inference. The Touch Plus PC page links to the same PCM section: "The Meta Quest Touch Plus Controller also supports the PCM API for haptic playback." — [Meta: Touch Plus (PC native)](https://developers.meta.com/horizon/documentation/native/pc/native-touch-plus-controllers)

**PCM spec details (Khronos)**
- **`XrHapticPcmVibrationFB` fields:** `bufferSize`, `buffer` (floats in [-1, 1]), `sampleRate`, `append` and `samplesConsumed`.
- **append = false:** existing samples are cleared and a new effect starts. A non-PCM effect, or a PCM effect sent with append = false, cancels whatever is playing.
- **append = true:** samples join the currently playing effect, and the runtime "must finish the previous samples before playing the new effect" (which may use a different `sampleRate`).
- **`samplesConsumed`:** filled in before `xrApplyHapticFeedback` returns.
- **Resampling:** the runtime may resample and keeps an internal buffer of `XR_MAX_HAPTIC_PCM_BUFFER_SIZE_FB` length.
- [Khronos: XrHapticPcmVibrationFB](https://registry.khronos.org/OpenXR/specs/1.1/man/html/XrHapticPcmVibrationFB.html); [Khronos: xrGetDeviceSampleRateFB](https://registry.khronos.org/OpenXR/specs/1.1/man/html/xrGetDeviceSampleRateFB.html)

**Constants and bindings (local check, pyopenxr 1.1.6501 `xr/constants.py`)**
- `MAX_HAPTIC_PCM_BUFFER_SIZE_FB = 4000` and `MAX_HAPTIC_AMPLITUDE_ENVELOPE_SAMPLES_FB = 4000`.
- `HAPTIC_PARAMETRIC_MAX_POINTS_TRANSIENTS_EXT = 500`, `HAPTIC_PARAMETRIC_VIBRATION_EXTEND_DURATION_EXT = 50000000` (50 ms), `HAPTIC_PARAMETRIC_FREQUENCY_MIN_HZ_EXT = 1` and `HAPTIC_PARAMETRIC_FREQUENCY_MAX_HZ_EXT = 1000`.
- `FREQUENCY_UNSPECIFIED = 0` and `MIN_HAPTIC_DURATION = -1`.
- `xr/typedefs.py` defines `HapticPcmVibrationFB` and `HapticAmplitudeEnvelopeVibrationFB` plus the parametric structs; `xr/functions.py` defines `get_device_sample_rate_fb`.
- Jon's current code (`spike0/record.py` line ~398) uses `xr.HapticVibration(duration=..., frequency=xr.FREQUENCY_UNSPECIFIED, amplitude=...)`.

**Latency over Link**
- **The one measurement found (Sabnis et al., CHI 2026):** Quest 3 over Link (USB), headset at 120 Hz, Unity 2022.3 with the Meta XR toolkit.
  - Method: tap the controller and time from the tap (seen by an external IMU) to the haptic pulse it triggers. That covers controller tracking, app logic, Link, the runtime and the actuator.
  - Result: **21.486 ± 1.426 ms** over 30 trials.
  - Controller sampling interval: 16.6 ms.
  - The authors judged this below the tactile temporal threshold, which they cite as "between 25 and 60 milliseconds".
  - [Sabnis et al. CHI '26, Sec. 3.2 and Appendix A](https://umtl.cs.uni-saarland.de/paper_preprints/sabnis-et-al-bimanual-haptics-pre-print-chi-2026.pdf)
- **Forum anecdotes (not verified):**
  - Link controller lag is usually GPU or encoding related, and USB encode bitrates of about 650 Mbps or more raise latency. — [Meta community forum](https://communityforums.atmeta.com/discussions/PairingConnection/meta-quest-link-latency/1365934)
  - Weak haptics over Link appear mainly when going through **SteamVR**. One fix was to turn off SteamVR's "Meta Plugin Compatibility". — [BigBox VR support](https://support.bigboxvr.com/hc/en-us/articles/32380950760724-How-to-fix-weak-haptics-on-Steam-with-Quest-2-and-Quest-3-headsets-connected-via-Link)
  - Roblox reports that PC VR haptics reach only about 5-10% of Quest 3 vibration power. — [Roblox devforum](https://devforum.roblox.com/t/controllers-vibration-works-poorely-on-pc-vr/3317416)

**Meta Haptics SDK and Haptics Studio**
- **Native SDK:** a C API (usable from "Rust and other languages that can call a C API") that plays `.haptic` clips "on a Meta Quest and other PCVR controllers".
  - It adapts to the hardware: "high-fidelity haptics when supported by the OpenXR runtime and controllers", otherwise "a fixed vibration frequency or a lower sample rate".
  - It supports amplitude and frequency modulation during playback, looping, several clips per controller with manual priority, and automatic resume of interrupted long clips.
  - Apps can instead call `xrApplyHapticFeedback` directly with PCM data.
  - The page was last updated 2024-11-25.
  - [Meta: Haptics Native SDK](https://developers.meta.com/horizon/documentation/native/experimental/exp-haptics-native/)
- **Cross-platform since v69:** Haptics SDK v69 added support for PCVR OpenXR runtimes, including SteamVR targets. Haptics Studio exports `.haptic`, `.ahap` (Apple Core Haptics) and `.wav`. The blog is dated 2024-12-04. — [Meta dev blog: cross-platform Haptics SDK](https://developers.meta.com/horizon/blog/cross-platform-support-haptics-studio-interaction-sdk-openxr-pcvr-meta-quest/)
- **The `.haptic` file:** described as JSON encoding amplitude, frequency, emphasis and duration, hardware-agnostic and forward compatible. — [Meta: OpenXR haptic feedback](https://developers.meta.com/horizon/documentation/native/android/mobile-openxr-haptic/); [Meta: Haptics Native SDK](https://developers.meta.com/horizon/documentation/native/experimental/exp-haptics-native/)
- **Haptics Studio app:** a desktop app for Windows and Mac with a Quest companion app for auditioning effects on the controllers. It can generate haptics from audio files. — [Meta: Haptics system](https://developers.meta.com/horizon/design/haptics-system/); [Meta dev blog: Haptics SDK and Studio](https://developers.meta.com/horizon/blog/haptics-sdk-studio-meta-quest-vr/)
- **Separate open-source renderer:** there is a lower-level `meta-haptics-sdk` library ("rendering and data processing") that runs on Windows, macOS, Linux and consoles. It states it lacks play, stop, pause and seek APIs. This comes from a mirror listing, not Meta docs. — [mirror listing](https://www.gitlink.org.cn/mirrors/meta-haptics-sdk)

### Inferences
- **Today's call cannot change pitch.** The `frequency` field is ignored, so Jon's current `xrApplyHapticFeedback(XrHapticVibration)` gives amplitude and duration only, at whatever carrier the runtime picks. Each new call from the 72-90 Hz loop also lands on a frame boundary, which adds up to about 11-14 ms of timing jitter to impacts the physics knows to the millisecond.
- **Recommended path for Python: PCM streaming.**
  1. Query `get_device_sample_rate_fb` once per session.
  2. Synthesize the waveform in numpy at that rate.
  3. Submit chunks with `append=True` from a small dedicated thread, for example every 5-10 ms with about 10-20 ms of lead.
  4. Place each impact at its exact sample offset, taken from the 1 kHz physics time.
  This removes frame jitter in exchange for a small fixed delay, and it gives full control of frequency, decay and noise. The 4000-sample cap (2 s at 2 kHz) is plenty per call. Use `samplesConsumed` to detect back-pressure.
- **Parametric is the fallback.** It is the device-agnostic path and supports transients natively. Its 50 ms extend duration and frame-rate guidance suggest a streaming model that suits authored clips better than physics-driven waveforms.
- **The Haptics SDK is not needed from Python.** It is a C library built around `.haptic` clips. Hand-parsing `.haptic` JSON exported from Studio and rendering it to PCM is likely simpler than binding the SDK through ctypes. Studio is still useful as an auditioning and authoring tool, including turning recorded puck and stick sounds into haptic drafts.
- **Avoid SteamVR.** Stay on the Meta OpenXR runtime (as now). SteamVR exposes none of these extensions, and the "weak haptics" anecdotes cluster there.

### Gaps
- **Unknown device sample rate.** The actual `xrGetDeviceSampleRateFB` value for Touch Plus on the PC runtime was not found in any doc; it needs a session with the headset connected. Meta's example uses a 2000 Hz source.
- **Unproven on Link.** No source confirms that `XR_EXT_haptic_parametric` actually renders correctly on Touch Plus over Link (it is listed locally; not tested). No source states whether PC behaviour matches the Android doc in every detail.
- **Unknown carrier for simple haptics and the amplitude envelope.** Which frequency the VCM plays for `XrHapticVibration` and amplitude-envelope effects is undocumented.
- **No standalone comparison.** No Link-versus-standalone haptic latency comparison was found, and no measurement of the haptic path alone (as opposed to Sabnis' tracking-to-actuation total).

---

## 3. Design techniques with evidence: impacts, scrape and texture, hardness and mass, sweet spot, two-hand distribution

### Takeaway
The strongest evidence supports three things:
- **Event-based transients for contact:** short decaying sinusoids whose amplitude scales with impact speed (Okamura; Kuchenbecker), which move virtual contact from "foam" toward "wood".
- **Hardness from frequency, decay and energy:** soft materials get low frequency and fast decay; hard ones get high frequency, longer ring and more high-frequency energy.
- **Speed-driven texture for sliding:** Culbertson; speed matters more than force.

A CHI 2026 study on the exact hardware (two Quest 3 controllers) shows that sending vibration to both hands, with high amplitude "crosstalk" and near-zero delay, makes two separate controllers feel like one rigid object. That applies directly to a two-handed stick.

### Cited Findings
**Impacts: event-based haptics**
- **Why added transients:** with position feedback alone, virtual tapping feels like "soft foam". Adding high-frequency transients that match the accelerations of real contact made virtual objects feel like real wood on foam in blind tapping tests, and realism ratings rose significantly. — [Kuchenbecker, Fiene, Niemeyer, "Event-Based Haptics and Acceleration Matching" (2005)](https://repository.upenn.edu/meam_papers/228); [same group, IEEE TVCG 2006 (PubMed)](https://www.ncbi.nlm.nih.gov/pubmed/16509381)
- **What shapes the transient:** Fiene and Kuchenbecker (2007) modelled how transients depend on impact velocity, impact acceleration and user grip force. That gives "a formula for generating open-loop, event-based force transients upon impact with a virtual surface". — [Fiene & Kuchenbecker, "Shaping Event-Based Haptic Transients…"](https://repository.upenn.edu/meam_papers/225)
- **The reality-based vibration model:** a decaying sinusoid, Q(t) = A(v)·e^(−Bt)·sin(ωt), with amplitude a function of impact velocity, fitted from accelerometer recordings of tapping real materials. Perceptual tuning produced parameters different from the raw recordings, partly because the display could not reproduce everything. — [Okamura, Cutkosky, Dennerlein, IEEE/ASME Trans. Mechatronics 2001 (Harvard project page)](https://biorobotics.harvard.edu/pastprojects/asme.html); [abstract](https://dissem.in/p/29467505/reality-based-models-for-vibration-feedback-in-virtual-environments)

**Hardness**
- **Zamani et al. (eLife reviewed preprint, 2026):**
  - Signals tested: recorded taps, decaying sinusoids and Ricker wavelets, about 50 ms bursts, band 30-1000 Hz.
  - Example parameters: foam τ = 5 ms at 85 Hz; metal τ = 20 ms at 400 Hz.
  - Taps with more spectral (vibratory) energy were judged harder, and waveform type did not matter. When energy and frequency were crossed, rendered energy predicted choices (OR ≈ 2.76).
  - The authors propose 100-300 Hz energy as a hardness proxy.
  - The eLife assessment rates the evidence "incomplete" for energy being the dominant cue.
  - [Zamani, …, Culbertson, Hartcher-O'Brien (2026), eLife](https://elifesciences.org/reviewed-preprints/111461)
- **Other hardness cues:** damped vibration frequency and decay, and the presence of a secondary vibration mode, raise perceived hardness; stiffness, frequency and viscosity correlate with it. These are search-snippet summaries of follow-up studies; the full papers were not reviewed. — [Okamura-line summary](https://acnpsearch.tweb-dev.unibo.it/singlejournalindex/84647575)

**Texture and sliding**
- **Data-driven textures (Culbertson):** recorded tool vibrations become per-segment autoregressive models, interpolated in force-speed space at render time.
  - In a 15-participant study, removing **speed** responsiveness significantly reduced realism; removing **force** responsiveness did not.
  - The Penn Haptic Texture Toolkit publishes 100 texture models with data and code.
  - [Culbertson et al. (Penn repository)](https://repository.upenn.edu/handle/20.500.14332/40005); [search summary of the 2013-2015 papers](https://arxiv.org/pdf/2212.13332v3.pdf)

**Two hands on one object**
- **Sabnis et al., CHI 2026: "Bimanual Vibrotactile Crosstalk", on two stock Quest 3 controllers over Link.**
- **The idea:** vibration "grains" triggered by motion are sent from the moving hand to the other hand with tunable crosstalk in amplitude, frequency, grain count and delay.
- **Stimulus:** one sine cycle at 120 Hz (8.33 ms) per grain, at amplitude 1.0. 120 Hz was chosen as within Pacinian sensitivity. Their authoring tool exposes 80-200 Hz.
- **Connectedness:** when only one hand moved, the feeling that both hands held one object went from 0-12.5% with no crosstalk to 87.5% with any crosstalk.
- **Mapping:** relative mapping (driven by the distance between the hands) felt more connected and natural than absolute mapping (each hand on its own).
- **Amplitude crosstalk as stiffness:**
  - Low (33%): "fragile, loose, slipping", like "a metal pipe… but my right hand is a bit wet and slips".
  - Medium (66%): "stable, control, chain-like".
  - High (100%): "stiff… heavily engineered hinge", "robust", "requiring more exertion".
- **Delay crosstalk:** 50 ms read as "immediate", like elastic bands and taut couplings; longer delays read as "layered or coiled mechanisms".
- **Sample sizes:** 16 participants in Study 1 and 12 in Study 2, blindfolded and with no visuals.
- **Code:** published at github.com/sensint/biHaptics.
- [Sabnis et al. CHI '26 preprint](https://umtl.cs.uni-saarland.de/paper_preprints/sabnis-et-al-bimanual-haptics-pre-print-chi-2026.pdf)

**Meta's design vocabulary**
- **Elements:** amplitude, frequency ("higher frequencies feel more continuous, and lower frequencies feel softer"), envelope, modulation, and "emphasis points (transients)" for clicks, taps and impacts.
- **Mappings:** "Hard: use a sharp tap or high-intensity vibration"; "Soft: use light, subtle buzz"; "Rough texture: use jagged or pulsing vibrations"; "Smooth texture: even, continuous vibration, or none at all".
- [Meta: Haptics design guidelines](https://developers.meta.com/horizon/resources/haptics-design-guidelines/); [Meta: Haptics best practices](https://developers.meta.com/horizon/design/haptics-best-practices/)
- **Transients in Meta's API:** a short, strong, "clicky" burst layered on top of the amplitude and frequency curves. — [Meta: Unity haptics APIs](https://developers.meta.com/horizon/documentation/unity/unity-haptics-apis/)
- **Studio practice (unofficial tutorial):** add emphasis at the onset of a strike and again just after, to suggest impact and then resonance. — [Brown VR wiki: Haptics Studio tutorial](https://www.vrwiki.cs.brown.edu/vr-development-software/vr-user-experience/meta-haptics-studio-interactions-tutorial)

### Inferences
These are design proposals for the hockey case, built from the evidence above. They are not tested.

- **Puck hitting the blade (heavy rubber on light composite):**
  - Render a decaying sinusoid per contact event, with amplitude proportional to the normal relative velocity (or to the 1 kHz contact impulse, clipped and compressed).
  - Rubber puck: low carrier (about 80-150 Hz) with fast decay (τ about 5-10 ms), close to Zamani's "foam" parameters, for a "thud".
  - Add a short higher-frequency component (about 250-400 Hz, τ 2-5 ms) whose share grows with impact speed, so hard passes and one-timers feel crisper and "harder" (more high-frequency energy, per Zamani).
  - Keep each event around 30-60 ms. Longer tails make it feel buzzy.
- **Light flexible stick versus the heavy puck:** the composite stick's own ringing could be a second, longer, lower-amplitude decaying mode after the puck transient (Okamura's secondary-mode finding: a secondary mode raises perceived hardness). Its frequency and decay should come from stick vibration physics, which another researcher covers.
- **Blade on ice (scrape and texture):**
  - Drive a continuous, low-level texture from **blade sliding speed**, which Culbertson found to be the dimension that matters. Normal load is optional, from the contact force.
  - Options: band-limited noise, or Sabnis-style grains triggered per distance travelled (grains per metre), so faster strokes produce denser pulses.
  - Keep scrape amplitude well below impact peaks, for example 10-25%, so puck contacts stay distinct.
- **"Sweet spot" cue (inference only):** a clean hit gets a short, well-damped transient with little leftover ringing; an off-centre (toe or heel) hit gets a longer, higher-frequency "sting" tail and slightly lower main amplitude. This mirrors bat and racket physics but is untested for controller haptics.
- **Two hands on one stick:**
  - Treat it like Sabnis' high-crosstalk, zero-delay case: both controllers vibrate for every blade event, which reads as a rigid, connected object.
  - Weight amplitude by each hand's distance from the blade, so the lower hand (nearer the blade) gets more. For example, the lower hand at 100% and the top hand at 60-80%. Do not go to about 33%, which read as "loose / slipping".
  - Wave travel along a composite shaft takes well under 1 ms, so use zero delay. Sabnis' 50 ms delay already read as elastic.
  - A tiny frequency difference between hands, such as the top hand a bit lower, is an untested option.
- **Use timing, not just amplitude.** The Quest 2 rule "louder = harder" now has a better alternative on Touch Plus: spectrum (frequency and decay) separates rubber from hard contact. This is cheap to test in A/B blind trials using Jon himself as the subject.

### Gaps
- **No hockey or puck haptic data.** No published acceleration recordings of a puck on a stick blade, and no ice-scrape vibration spectra, were found. Recording these with a stick-mounted accelerometer (or a phone taped to a real stick) would give data-driven templates in the style of Okamura and Culbertson.
- **No study on which hand should feel what.** No study compares dominant and non-dominant hands, or top and bottom hand, for haptics on a two-handed held tool. Sabnis covers stretching, bending and twisting, not impacts on a rigid tool.
- **No sweet-spot evidence.** No study tests a vibrotactile sweet-spot cue on VR controllers.
- **Full-text details not reviewed.** The exact Fiene and Kuchenbecker formula and the Okamura parameter tables were not available from the abstracts found.

---

## 4. Audio-haptic coupling: generating haptics from audio, timing alignment, simultaneity thresholds

### Takeaway
Deriving haptics from the impact audio is the industry workflow (Meta Haptics Studio's audio analysis, used in Asgard's Wrath 2 and Home Sports), and it keeps sound and touch consistent. For timing, impact-type audio and vibration pairs tolerate only about −10 to +40 ms. The window narrows at stronger vibration. Unverified search reports put it at 180-450 ms for button-like or active-touch tasks. Over Link, tracking-to-vibration was about 21.5 ms, so haptics and audio should come from the same event timestamp, and haptics should never lag noticeably.

### Cited Findings
- **Audio-to-vibration delay for impacts:** at the lowest vibration level, the most acceptable delays ran from about −10 ms (vibration first) to +40 ms (vibration after). Stronger vibration narrowed the window, and judging "naturalness" instead of strict simultaneity widened it. — [Canadian Acoustics (JCAA) paper on audio-vibration synchrony](https://jcaa.caa-aca.ca/index.php/jcaa/article/download/1661/1408/1798)
- **Driving study:** about 16 ms of system latency, with audio lagging haptics even when sent together; the authors compensated. — [arXiv 2307.05451](https://arxiv.org/pdf/2307.05451)
- **Classic definitions:** Altinsoy's work defines auditory-tactile simultaneity thresholds and the point of subjective simultaneity, and compares methods. — [Altinsoy 2002](https://tu-dresden.de/ing/elektrotechnik/ias/aha/ressourcen/dateien/professur/publikationen/Altinsoy2002_-_On_the_perception_of_the_synchrony_for_auditory-tactile_stimuli.pdf); [Altinsoy 2003](https://tu-dresden.de/ing/elektrotechnik/ias/aha/ressourcen/dateien/professur/publikationen/Altinsoy2003_-_Perceptual_aspects_of_auditory-tactile_asynchrony.pdf)
- **Tactile temporal threshold:** "between 25 and 60 milliseconds" for time-based tactile sensitivity, as cited by Sabnis et al.; the Quest 3 over Link measured 21.5 ms motion-to-actuation. — [Sabnis et al. CHI '26](https://umtl.cs.uni-saarland.de/paper_preprints/sabnis-et-al-bimanual-haptics-pre-print-chi-2026.pdf)
- **Meta's timing rules:** "Synchronize haptics with audio and visual feedback with minimal delay"; "Avoid delays, missing feedback, or any asynchrony"; do not play haptics without a matching visual or audio cue; pair soft sounds with soft haptics. No numbers are given. — [Meta: Haptics best practices](https://developers.meta.com/horizon/design/haptics-best-practices/)
- **Haptics Studio workflow:** it imports audio files, analyses them into amplitude and frequency envelopes plus emphasis points, and allows manual edits. — [Meta dev blog: Haptics SDK and Studio](https://developers.meta.com/horizon/blog/haptics-sdk-studio-meta-quest-vr/); [Resolution Games blog](https://www.resolutiongames.com/blog/how-cutting-edge-technologies-are-taking-home-sports-to-the-next-level-1)
- **Asgard's Wrath 2 audio pipeline:** Sanzaru routed haptic PCM through FMOD so one audio parameter drove both sound and vibration (for example the bow-string pull). — [Meta dev blog: Asgard's Wrath 2 haptics](https://developers.meta.com/vr/blog/asgards-wrath2-and-haptics-studio/)

### Inferences
- **One event, two outputs.** Emit sound and vibration from the same physics contact event with the same impact-speed parameter, and derive the haptic waveform's envelope from the same synthesis as the audio. Jon's `sounds.py` and `synth.py` already synthesize audio, so a shared generator is natural.
- **Lag budget.** Aim for haptic onset no later than about 20-40 ms after the visual and audio contact, and never before the visual. The tight −10/+40 ms window applies to exactly this kind of short impact. Pre-scheduling PCM with sample-accurate offsets helps stay inside it.
- **Measure audio delay too.** Link audio latency is also unknown and should be measured; if audio lags noticeably, the haptic may need a small deliberate delay rather than none.

### Gaps
- **Unknown audio latency over Link.** No source gave end-to-end Link audio latency, so the audio-versus-haptic offset on Jon's setup is unknown. It can be measured with a microphone plus an accelerometer.
- **No hockey-specific data.** No study measures audio-tactile simultaneity specifically for a held tool striking an object in VR.
- **Unverified wider windows.** Search snippets attributed to Brahimaj et al. (IEEE Haptics Symposium and World Haptics, 2023) report much wider windows: about 179 ms (audio first) and 451 ms (haptic first) for virtual buttons, and about 200-233 ms for active sliding touch. The original papers were not retrieved, so treat these as unverified. They suggest the window widens greatly for button-like or active-touch tasks, compared with discrete impacts.

---

## 5. Practical lessons from shipped VR games and developers

### Takeaway
The documented, credible lessons come mostly from Meta's own developer blog:
- Let the audio team own haptics.
- Generate haptics from finished audio, then add emphasis by hand.
- Use haptics as a "sub-woofer" layer that glues big moments together.
- Hold back so they are not overused.
- Make each sport action distinct.

Detailed numeric postmortems (frequencies, amplitudes) for praised sports or rhythm games were not found.

### Cited Findings
- **Asgard's Wrath 2 (Sanzaru, Quest 3):**
  - Over 700 unique, audio-driven haptic assets, made in Meta Haptics Studio.
  - Haptics moved under the audio team to end uneven quality from many disciplines.
  - Workflow: bulk-import existing SFX, rely on Studio's analysis, add manual emphasis only where needed, and do one late pass after audio was final.
  - Results: Quest 3's "full-frequency" haptics raised immersion; "the haptics became the 'sub' and really glued things together".
  - Caution: "We needed to be careful to not over use haptics features in these sections."
  - [Meta dev blog: Asgard's Wrath 2 haptic design journey](https://developers.meta.com/vr/blog/asgards-wrath2-and-haptics-studio/)
- **Home Sports (Resolution Games):**
  - Used Haptics Studio to build haptics from sound files, then edited frequency and emphasis.
  - Argues each action needs distinct feedback, giving "a hockey slapshot with a stick" versus a bowling toss versus soft and hard pickleball hits as examples.
  - "Without the tactile sensation of 'feeling' what's happening, interactions can lack authenticity."
  - No numbers given.
  - [Resolution Games blog](https://www.resolutiongames.com/blog/how-cutting-edge-technologies-are-taking-home-sports-to-the-next-level-1)
- **Other users of Meta's cross-platform haptics:** POPULATION: ONE (BigBox VR) and Max Mustard (Toast Interactive), with Max Mustard shipping to PC and console VR. — [Meta dev blog: cross-platform Haptics SDK](https://developers.meta.com/horizon/blog/cross-platform-support-haptics-studio-interaction-sdk-openxr-pcvr-meta-quest/)
- **Meta best-practice list:**
  - Use "whitespace" (pauses so the skin rests).
  - Accentuate key moments rather than every interaction.
  - Keep frequent interactions subtle.
  - Avoid long or overlapping effects and continuous vibration.
  - Keep patterns consistent and clearly distinct.
  - Make intensity adjustable or mutable.
  - "The best ones often go unnoticed until they're missing."
  - [Meta: Haptics best practices](https://developers.meta.com/horizon/design/haptics-best-practices/)

### Inferences
- **For Jon's trainer:**
  - Puck contacts (receive, shoot, deflect) are the "key moments" that deserve the strongest, most distinct signatures.
  - Continuous ice contact should be the quiet bed underneath.
  - A user-adjustable master gain plus a separate scrape gain follows Meta's advice and lets him tune for numbness.

### Gaps
- **No numeric postmortems.** None were found for praised controller-haptics games (Beat Saber, Pistol Whip, Eleven Table Tennis, Thrill of the Fight, Racket Club, Gorilla Tag, and so on).
- **No GDC talk content.** A GDC talk specifically on Quest Touch Plus haptic design was not located in this pass; the GDC Vault would be the next place to look.

---

## 6. Limitations and pitfalls

### Takeaway
Controller vibration cannot render sustained force, weight, resistance or the pull of a heavy puck on the blade. A 2024 CHI study found that adding vibration did not improve perceived weight change; visual "pseudo-haptics" did. Pitfalls:
- Vibrotactile adaptation and numbness from prolonged vibration.
- Masking and drowning when pulses are too frequent or continuous.
- Weaker or broken haptics when running through SteamVR.
- Frame-quantized timing.

Asymmetric-vibration "pulling" illusions exist in research on voice-coil devices, but are unproven on Quest controllers.

### Cited Findings
- **Weight:** Stellmacher et al. (CHI 2024, 18 participants) found pseudo-haptic changes to the control-display ratio produced perceived weight change, but "additional vibrotactile feedback did not improve weight change perception". They note consumer controllers have "limited vibrotactile feedback" for weight. — [Stellmacher et al., "Experiencing Dynamic Weight Changes in VR Through Pseudo-Haptics and Vibrotactile Feedback"](https://alexandria.unisg.ch/entities/publication/d530560f-94e0-4952-a602-40613242a2dd/details)
- **Fingertip vibration and weight:** a 2022 study saw a trend toward heavier perception with fingertip vibration, without a statistically significant behavioural effect. — [Frontiers in VR 2022](https://frontiersin.org/articles/10.3389/frvir.2022.797993/full)
- **Mechanical alternatives** that change trigger resistance (Triggermuscle) or controller weight (PumpVR) do work, but they modify the hardware. — [Triggermuscle (Frontiers 2022)](https://hci.uni-bremen.de/wp-content/uploads/2022/03/Triggermuscle_Frontiers.pdf); [PumpVR (CHI 2023)](https://epub.uni-regensburg.de/54245/1/3544548.3581172.pdf)
- **Asymmetric vibration illusion:** asymmetric vibration produces an illusory pulling force, attributed to nonlinear perception. It has been shown with handheld voice-coil prototypes (a single voice coil giving virtual force in 8 directions). It works best when the phase difference between the fundamental and the second harmonic is near 0° or −180°. These are custom research devices, not Quest controllers. — [UVA thesis](https://libraetd.lib.virginia.edu/public_view/4j03d078m); [Tanabe et al., pulling illusion and phase difference](https://aminer.org/pub/5ff680d3d4150a363cb52f4c/pulling-illusion-based-on-the-phase-difference-of-the-frequency-components-of)
- **Adaptation:**
  - Pacinian sensitivity peaks near 250 Hz, with the Pacinian channel covering about 35-500 Hz.
  - Prolonged vibration (around 10 minutes) raises later detection thresholds.
  - Adaptation is channel-specific and does not transfer across psychophysical channels.
  - One fingertip study found 50 Hz adapted less than 250 Hz.
  - These are summaries of several sources; magnitudes for the palm were not found.
  - [Vibrotactile frequency characteristics: adaptation and masking](https://rd.springer.com/chapter/10.1007/978-1-4613-3039-4_10); [PMC review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11814341); [hand vibrotactile thresholds 8-250 Hz (2014)](https://link.springer.com/10.1007/s00421-014-2885-y)
- **Overuse and fatigue:** Meta warns against intense, continuous, long or overlapping effects (fatigue) and recommends whitespace. — [Meta: Haptics best practices](https://developers.meta.com/horizon/design/haptics-best-practices/)
- **Battery:** Meta says only "Consider Hardware Dependency and Energy Consumption". — [Meta: Haptics best practices](https://developers.meta.com/horizon/design/haptics-best-practices/)
- **PC-path anecdotes (forum, unverified):**
  - Haptics much weaker on PC via SteamVR or Air Link than standalone. — [VRChat feedback](https://feedback.vrchat.com/udon/p/equalize-haptics-across-platforms); [BigBox VR support](https://support.bigboxvr.com/hc/en-us/articles/32380950760724-How-to-fix-weak-haptics-on-Steam-with-Quest-2-and-Quest-3-headsets-connected-via-Link)
  - No vibration at all in some engines over Air Link. — [Unigine forum](https://developer.unigine.com/forum/topic/8355-no-vibration-in-vr-with-a-quest)

### Inferences
- **What vibration cannot do:**
  - The heavy puck's momentum and the stick's flex under load cannot be felt as force. Vibration can only signal that contact happened and what it was like (soft or hard, scraping or still).
  - Weight and "the puck is on my blade" must come from other channels: visual pseudo-haptics (slight lag or drag of the virtual blade under load, offset from the tracked controller, which Stellmacher showed can convey weight), audio, and the controller's own real mass.
  - Vibration should *punctuate*, not try to represent force.
- **Avoid numbness and masking:**
  - Do not run a constant scrape buzz. Gate it to actual sliding contact above a speed threshold, fade it in and out, and keep it quiet.
  - Consider putting scrape texture and puck impacts in different frequency bands so they stay distinguishable (adaptation is channel-specific).
  - Re-sending a pulse every render frame (72-90 Hz) while the blade touches the ice adds up to a continuous buzz that masks puck contacts. Use event onsets plus a quiet, continuous, speed-driven texture.
- **Asymmetric pull (experimental):** with PCM driving a VCM directly, a 2-harmonic asymmetric waveform for a "pull" cue (puck on the blade, stick drag) is technically possible. It is speculative: the axis of the Touch Plus actuator and its low-frequency response are unknown.

### Gaps
- **No Quest-specific limits found.** No data on Touch Plus battery drain from haptics, no data on thermal or duty-cycle limits of the VCM, and no measured adaptation figures for the palm under game-like duty cycles.
- **Asymmetric illusion untested.** No test of the asymmetric-vibration pulling illusion on Quest controllers was found.
- **Unknown cause of weak PC haptics.** No authoritative explanation was found for "weak haptics on PC" reports. They may be specific to SteamVR or to the engines involved; the native Meta runtime path Jon uses was not implicated in any source.
