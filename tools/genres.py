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
}
assert all(l in LABELS for v in TAGS.values() for l in v)
