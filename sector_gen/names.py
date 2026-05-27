import json
import random
from pathlib import Path

PHONEMES_DIR = Path(__file__).parent / 'phonemes'


def load_register(name: str) -> dict:
    path = PHONEMES_DIR / f"{name}.json"
    if not path.exists():
        available = sorted(p.stem for p in PHONEMES_DIR.glob('*.json'))
        raise ValueError(
            f"Unknown phoneme register {name!r}. Available: {', '.join(available)}"
        )
    return json.loads(path.read_text(encoding='utf-8'))


def _generate_syllable(register: dict, rng: random.Random) -> str:
    pattern = rng.choice(register['patterns'])
    result = []
    for i, ch in enumerate(pattern):
        if ch == 'V':
            result.append(rng.choice(register['vowels']))
        elif ch == 'C':
            has_vowel_before = any(c == 'V' for c in pattern[:i])
            has_vowel_after = any(c == 'V' for c in pattern[i + 1:])
            if not has_vowel_before:
                result.append(rng.choice(register['initial_consonants']))
            elif has_vowel_after:
                result.append(rng.choice(register['medial_consonants']))
            else:
                result.append(rng.choice(register['final_consonants']))
    return ''.join(result)


def generate_name(register: dict, seed_string: str) -> str:
    rng = random.Random(seed_string + '-name')
    count = rng.choice(register['syllable_count'])
    syllables = [_generate_syllable(register, rng) for _ in range(count)]
    if count > 1:
        joiner = rng.choice(register.get('joining_vowels', ['']))
        name = joiner.join(syllables)
    else:
        name = syllables[0]
    return name.capitalize() if name else 'Unknown'


def test():
    registers = ['default', 'angular', 'liquid', 'eastern']
    for reg_name in registers:
        reg = load_register(reg_name)
        names = [generate_name(reg, f'TEST-XX-A{i:04d}') for i in range(20)]
        for n in names:
            assert n, f"Empty name from register {reg_name}"
            assert 1 <= len(n) <= 30, f"Name {n!r} has unexpected length from register {reg_name}"
    print("names: all tests passed")
