# Raw Audio Inputs

Place performance recordings here when you want to complement the symbolic analysis with audio features.

## Recommended Formats

- `WAV`
- `FLAC`
- `AIFF`
- `MP3` only when lossless versions are not available

## Suggested Naming

```text
suite_01_prelude_g_major_bwv1007_reference.flac
suite_02_prelude_d_minor_bwv1008_reference.wav
```

## What The Audio Layer Is For

- tempo and pulse extraction
- loudness and metering
- key estimation from performance audio
- spectral descriptors useful for interpretation and sonority comparison

## What The Audio Layer Is Not For

- reliable Roman numeral analysis on its own
- detailed cadence labeling without score context
- voice-leading reconstruction from stereo piano audio alone

## Recommended Workflow

1. gather clean recordings from reliable sources
2. normalize filenames
3. copy them into this folder
4. run `python main.py analyze-audio-corpus --input-dir data/audio/raw`

## Source Ideas

- IMSLP currently lists six MP3 recordings on the suite collection page, one for each suite, under the recordings section: [IMSLP BWV 1007-1012](https://imslp.org/wiki/6_Cello_Suites%2C_BWV_1007-1012_%28Bach%2C_Johann_Sebastian%29)
- if you obtain higher-quality commercial or personal reference recordings yourself, prefer lossless formats for analysis
