# Genre labels per album (book number -> labels). Shown as filter chips on the site;
# an album can carry several. Applied to dist/albums.json by store.rebuild_index().
# Use only labels from LABELS so the filter stays tidy. Subjective by nature: the owner reviews.
LABELS = ["רוק'נרול", "רוק", "רוק אלטרנטיבי", "פרוגרסיב ופסיכדליה", "פאנק וניו וויב", "מטאל", "פופ",
          "סטנדרטים וקברט", "סול ופאנק", "בלוז", "ג'אז", "קאנטרי", "פולק", "היפ הופ", "אלקטרוני", "רגאיי", "מוזיקת עולם"]
R, ROCK, POP, STD, SOUL, BLUES, JAZZ, COUNTRY, FOLK, WORLD = "רוק'נרול", "רוק", "פופ", "סטנדרטים וקברט", "סול ופאנק", "בלוז", "ג'אז", "קאנטרי", "פולק", "מוזיקת עולם"
ALT, PSYCH, PUNK = "רוק אלטרנטיבי", "פרוגרסיב ופסיכדליה", "פאנק וניו וויב"
TAGS = {
  1: [STD], 2: [R], 3: [COUNTRY, FOLK], 4: [R, JAZZ], 5: [R], 6: [JAZZ], 7: [STD], 8: [R], 9: [JAZZ], 10: [JAZZ],
  11: [WORLD, JAZZ], 12: [JAZZ], 13: [WORLD, JAZZ], 14: [R], 15: [WORLD, JAZZ], 16: [JAZZ, STD], 17: [FOLK], 18: [JAZZ], 19: [JAZZ, STD], 20: [SOUL, JAZZ],
  21: [JAZZ], 22: [COUNTRY], 23: [JAZZ], 24: [FOLK], 25: [R], 26: [WORLD], 27: [R, COUNTRY], 28: [JAZZ, SOUL], 29: [BLUES], 30: [JAZZ],
  31: [COUNTRY, SOUL], 32: [SOUL], 33: [JAZZ, WORLD], 34: [COUNTRY], 35: [ROCK], 36: [FOLK], 37: [POP], 38: [SOUL], 39: [JAZZ], 40: [SOUL],
  41: [JAZZ, WORLD], 42: [ROCK, POP], 43: [WORLD, STD], 44: [SOUL], 45: [POP, SOUL], 46: [ROCK, BLUES], 47: [COUNTRY], 48: [R], 49: [ROCK], 50: [FOLK, ROCK],
  53: [JAZZ],
  51: [SOUL], 52: [ROCK, POP], 54: [BLUES], 55: [ROCK, POP], 56: [FOLK], 57: [ROCK, FOLK], 58: [ROCK, FOLK], 59: [ROCK], 60: [ROCK, PSYCH],
  61: [POP, ROCK], 62: [FOLK], 63: [ROCK, PSYCH], 64: [ROCK, FOLK], 65: [ROCK, PUNK], 66: [ROCK, POP], 67: [POP, FOLK], 68: [ROCK], 69: [ROCK, PSYCH], 70: [ROCK, BLUES],
  71: [FOLK, POP], 72: [PSYCH, ROCK], 73: [BLUES, ROCK], 74: [ROCK, BLUES], 75: [JAZZ, STD], 76: [WORLD, JAZZ], 77: [FOLK, POP], 78: [ROCK, PSYCH], 79: [PSYCH, ROCK], 80: [ROCK, FOLK, COUNTRY],
  81: [ROCK, FOLK], 82: [ROCK, PSYCH], 83: [BLUES, ROCK, PSYCH], 84: [FOLK, ROCK], 85: [POP, ROCK], 86: [FOLK, PSYCH], 87: [PSYCH, FOLK], 88: [ROCK, PSYCH], 89: [PSYCH], 90: [ROCK, POP],
  91: [ROCK, ALT], 92: [STD, WORLD], 93: [ROCK, PSYCH], 94: [ROCK, PSYCH], 95: [SOUL, POP], 96: [PSYCH, ROCK], 97: [ROCK, POP], 98: [FOLK, PSYCH], 99: [COUNTRY], 100: [ROCK, PSYCH, BLUES],
  101: [PSYCH, ROCK], 102: [COUNTRY], 103: [WORLD], 104: [ROCK, ALT], 105: [ROCK, PSYCH, BLUES], 106: [SOUL], 107: [ROCK, BLUES], 108: [ROCK, PSYCH], 109: [FOLK, PSYCH], 110: [ROCK, POP],
  111: [WORLD], 112: [PSYCH, WORLD], 113: [ROCK, PSYCH, BLUES], 114: [FOLK], 115: [COUNTRY], 116: [POP, SOUL], 117: [SOUL], 118: [ROCK, BLUES, PSYCH], 119: [ROCK, PSYCH, COUNTRY], 120: [ROCK, BLUES, PSYCH],
  121: [PSYCH, ROCK], 122: [BLUES, PSYCH, SOUL], 123: [ROCK, PSYCH], 124: [PSYCH, ROCK], 125: [FOLK, POP], 126: [ROCK, PSYCH], 127: [ROCK, FOLK, COUNTRY], 128: [ROCK, BLUES], 129: [WORLD, PSYCH], 130: [POP, STD],
  131: [POP, PSYCH], 132: [FOLK, JAZZ], 133: [COUNTRY, ROCK], 134: [ROCK, PSYCH], 135: [ROCK, COUNTRY], 136: [ROCK, BLUES, PSYCH], 137: [ROCK, BLUES], 138: [FOLK, ROCK], 139: [ROCK, JAZZ], 140: [COUNTRY, ROCK],
  141: [COUNTRY], 142: [ROCK, COUNTRY], 143: [ROCK, POP], 144: [ROCK], 145: [JAZZ], 146: [POP, ROCK], 147: [FOLK], 148: [ROCK, BLUES], 149: [FOLK], 150: [SOUL, POP],
}
assert all(l in LABELS for v in TAGS.values() for l in v)
