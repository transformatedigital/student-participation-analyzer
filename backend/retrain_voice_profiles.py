#!/usr/bin/env python3
"""
Retrain voice profiles with all available clean Ileana clips (11 clips)
"""

import json
import numpy as np
from pathlib import Path
import librosa
import warnings
warnings.filterwarnings('ignore')

CLIPS_DIR = Path("/Users/santi/clase-analytics/data/clases/2026-03-31/audio_clips")
AUDIO_FILE = Path("/Users/santi/clase-analytics/data/clases/2026-03-31/audio_unificado.m4a")
OUTPUT_FILE = Path("/Users/santi/clase-analytics/data/clases/2026-03-31/voice_training_profiles.json")

# speaker_clip_7 is Aryang — all others (1-6, 8-12) are clean Ileana
ILEANA_CLIPS = [f"speaker_clip_{n}.mp3" for n in [1,2,3,4,5,6,8,9,10,11,12]]
STUDENT_CLIPS = {
    'mega':    ["student2_clip_01.mp3"],
    'grace':   ["student2_clip_04.mp3"],
    'chilaka': ["student2_clip_08.mp3", "student2_clip_09.mp3"],
    'aryang':  ["aryang_reference.mp3"],
}

def extract_features(y, sr):
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    spec_rolloff  = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    zcr           = librosa.feature.zero_crossing_rate(y)[0]
    chroma        = librosa.feature.chroma_cqt(y=y, sr=sr)
    rms           = librosa.feature.rms(y=y)[0]

    f = np.concatenate([
        mfcc.mean(axis=1), mfcc.std(axis=1),
        [spec_centroid.mean(), spec_centroid.std()],
        [spec_rolloff.mean(),  spec_rolloff.std()],
        [zcr.mean(), zcr.std()],
        chroma.mean(axis=1),
        [rms.mean(), rms.std()]
    ])
    return (f - f.mean()) / (f.std() + 1e-8)

def build_profile(file_list):
    feats = []
    for fname in file_list:
        p = CLIPS_DIR / fname
        if p.exists():
            try:
                y, sr = librosa.load(str(p), sr=None, mono=True)
                feats.append(extract_features(y, sr))
            except:
                pass
    return np.mean(feats, axis=0) if feats else None, len(feats)

def main():
    print("🎤 RETRAINING VOICE PROFILES")
    print("=" * 70)

    profiles = {}

    # ---- Ileana (11 clean reference clips) ----
    print(f"\n  Building ILEANA profile ({len(ILEANA_CLIPS)} clips)...", end=" ")
    feat, n = build_profile(ILEANA_CLIPS)
    if feat is not None:
        profiles['ileana'] = {'name': 'Ileana (Teacher)', 'clips': n, 'features': feat.tolist()}
        print(f"✅  ({n} clips used)")

    # ---- Students ----
    for speaker, files in STUDENT_CLIPS.items():
        print(f"  Building {speaker.upper()} profile ({len(files)} clips)...", end=" ")
        feat, n = build_profile(files)
        if feat is not None:
            profiles[speaker] = {'name': speaker.capitalize(), 'clips': n, 'features': feat.tolist()}
            print(f"✅  ({n} clips used)")

    # ---- Full audio sliding-window ----
    print(f"\n📊 Analyzing full audio with {len(profiles)} profiles")
    print(f"  Loading {AUDIO_FILE.name}...")
    y, sr = librosa.load(str(AUDIO_FILE), sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)
    print(f"  Duration: {duration/60:.1f} min  ({duration:.0f} s)")

    WS = int(3.0 * sr)
    HOP = int(1.0 * sr)
    total = (len(y) - WS) // HOP

    print(f"  Classifying {total} windows ", end="", flush=True)
    tally = {sp: 0 for sp in profiles}

    for i in range(total):
        if i % max(1, total // 20) == 0:
            print(".", end="", flush=True)
        win = y[i*HOP : i*HOP + WS]
        wf  = extract_features(win, sr)
        best, best_d = None, float('inf')
        for sp, prof in profiles.items():
            d = np.linalg.norm(wf - np.array(prof['features']))
            if d < best_d:
                best_d, best = d, sp
        if best:
            tally[best] += 1

    print(" ✅")

    # ---- Results ----
    print(f"\n📈 RESULTS — {duration/60:.1f} min audio")
    print("-" * 50)
    for sp, cnt in sorted(tally.items(), key=lambda x: -x[1]):
        pct = cnt / total * 100
        bar = "█" * int(pct / 2)
        print(f"  {sp.upper():10} {bar:<30} {pct:5.1f}%  ({cnt} windows)")

    # ---- Save ----
    result = {
        'metadata': {
            'duration_minutes': round(duration/60, 1),
            'windows_analyzed': total,
            'reference_clips_ileana': len(ILEANA_CLIPS),
            'timestamp': '2026-04-28'
        },
        'profiles': profiles,
        'coverage': {sp: {'windows': c, 'percentage': round(c/total*100, 1)}
                     for sp, c in tally.items()},
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n✅ Saved → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
