from fontTools import ttLib
from fontTools.ttLib import newTable

def merge_missing_glyphs(primary_path: str, fallback_path: str, output_path: str):
    primary = ttLib.TTFont(primary_path)
    fallback = ttLib.TTFont(fallback_path)

    # Extract cmap (Unicode to glyph name mapping)
    primary_cmap = primary['cmap'].getcmap(3, 1).cmap  # Platform 3, Encoding 1 (Windows Unicode)
    fallback_cmap = fallback['cmap'].getcmap(3, 1).cmap

    primary_glyph_set = set(primary_cmap.keys())
    fallback_glyph_set = set(fallback_cmap.keys())

    # Find codepoints missing in primary but present in fallback
    missing_codepoints = fallback_glyph_set - primary_glyph_set

    # Prepare to copy glyphs
    fallback_glyf = fallback['glyf']
    primary_glyf = primary['glyf']
    primary_hmtx = primary['hmtx']
    fallback_hmtx = fallback['hmtx']

    for codepoint in missing_codepoints:
        glyph_name = fallback_cmap[codepoint]

        # Copy glyph data
        if glyph_name not in primary_glyf:
            primary_glyf[glyph_name] = fallback_glyf[glyph_name]
            primary_hmtx[glyph_name] = fallback_hmtx[glyph_name]

        # Update cmap to include the new glyph
        primary_cmap[codepoint] = glyph_name

    # Save updated font
    primary.save(output_path)
    print(f"Saved merged font with fallback to {output_path}")

