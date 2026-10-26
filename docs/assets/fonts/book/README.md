# Book typefaces

PDF and EPUB exports embed static font faces for consistent rendering:

- **Source Serif 4**: English text, headings, bold, and italic. Original files from [Adobe’s Source Serif repository](https://github.com/adobe-fonts/source-serif/tree/release/TTF).
- **Noto Serif Malayalam**: Malayalam text, regular and bold. Original files from [Noto’s font repository](https://github.com/notofonts/noto-fonts/tree/main/hinted/ttf/NotoSerifMalayalam).

Noto Serif Tamil regular and bold are included as fallbacks for Tamil characters
present in the source, also from the Noto font repository.

The upstream font files are unchanged. `manifest.json` records versions, download
URLs, and SHA-256 checksums. All families use the SIL Open Font License 1.1; the
corresponding OFL files are included here, and the fonts retain their embedded
license metadata. These typefaces are used for book exports; the website and Anki
font choices are unchanged.
