/** Mapping from our 3-letter team codes to ISO 3166-1 alpha-2 (lowercase) for flagcdn.com. */
export const ISO2: Record<string, string> = {
  USA: "us", MEX: "mx", CAN: "ca",
  ARG: "ar", FRA: "fr", ESP: "es", ENG: "gb-eng", BRA: "br", POR: "pt",
  NED: "nl", BEL: "be", GER: "de", CRO: "hr", ITA: "it", MAR: "ma",
  COL: "co", URU: "uy", JPN: "jp", SUI: "ch", SEN: "sn", IRN: "ir",
  KOR: "kr", DEN: "dk", AUS: "au", AUT: "at", POL: "pl", UKR: "ua",
  TUR: "tr", NOR: "no", EGY: "eg", ALG: "dz", NGA: "ng", ECU: "ec",
  PAR: "py", KSA: "sa", QAT: "qa", IRQ: "iq", UZB: "uz", CIV: "ci",
  CMR: "cm", GHA: "gh", TUN: "tn", CRC: "cr", PAN: "pa", JAM: "jm",
  NZL: "nz", BOL: "bo", COD: "cd",
  RSA: "za", CZE: "cz", BIH: "ba", HAI: "ht", SCO: "gb-sct", CUW: "cw",
  SWE: "se", CPV: "cv", JOR: "jo",
};

/** flagcdn supports the special England "gb-eng" subdivision flag for the cross-of-St-George. */
export function flagUrl(code: string, w: 20 | 40 | 80 | 160 | 320 = 80): string {
  const iso = ISO2[code] ?? code.toLowerCase();
  if (iso.includes("-")) {
    // Subdivision flag (England, Scotland, Wales) — flagcdn supports as png at fixed sizes
    return `https://flagcdn.com/${w}x${Math.round((w * 3) / 4)}/${iso}.png`;
  }
  return `https://flagcdn.com/w${w}/${iso}.png`;
}

export function flagSrcset(code: string): string {
  const iso = ISO2[code] ?? code.toLowerCase();
  if (iso.includes("-")) {
    return `${flagUrl(code, 80)} 1x, ${flagUrl(code, 160)} 2x`;
  }
  return `https://flagcdn.com/w80/${iso}.png 1x, https://flagcdn.com/w160/${iso}.png 2x`;
}
