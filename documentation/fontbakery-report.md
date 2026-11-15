## FontBakery report

fontbakery version: 1.1.0







## Check results



<details><summary>[12] Kuhmard-Bold.otf</summary>
<div>
<details>
    <summary>⚠️ <b>WARN</b> Check GDEF mark glyph class doesn't have characters that are not marks. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/opentype.html#opentype-gdef-non-mark-chars">opentype/gdef_non_mark_chars</a></summary>
    <div>


> 
> Glyphs in the GDEF mark glyph class become non-spacing and may be repositioned
> if they have mark anchors.
> 
> Only combining mark glyphs should be in that class. Any non-mark glyph
> must not be in that class, in particular spacing glyphs.
> 




> Original proposal: https://github.com/fonttools/fontbakery/issues/2877





* ⚠️ **WARN** <p>The following non-mark characters should not be in the GDEF mark glyph class:
U+2028 and U+2029</p>
 [code: non-mark-chars]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Check math signs have the same width. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.html#math-signs-width">math_signs_width</a></summary>
    <div>


> 
> It is a common practice to have math signs sharing the same width
> (preferably the same width as tabular figures accross the entire font family).
> 
> This probably comes from the will to avoid additional tabular math signs
> knowing that their design can easily share the same width.
> 




> Original proposal: https://github.com/fonttools/fontbakery/issues/3832





* ⚠️ **WARN** <p>The most common width is 472 among a set of 4 math glyphs.
The following math glyphs have a different width, though:</p>
<p>Width = 442:
multiply, greater, less</p>
<p>Width = 451:
uni2260, uni00B1, uni00AC</p>
<p>Width = 499:
uni2248</p>
<p>Width = 414:
uni2264, uni2265</p>
 [code: width-outliers]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Does the font contain a soft hyphen? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.html#soft-hyphen">soft_hyphen</a></summary>
    <div>


> 
> The 'Soft Hyphen' character (codepoint 0x00AD) is used to mark
> a hyphenation possibility within a word in the absence of or
> overriding dictionary hyphenation.
> 
> It is sometimes designed empty with no width (such as a control character),
> sometimes the same as the traditional hyphen, sometimes double encoded with
> the hyphen.
> 
> That being said, it is recommended to not include it in the font at all,
> because discretionary hyphenation should be handled at the level of the
> shaping engine, not the font. Also, even if present, the software would
> not display that character.
> 
> More discussion at:
> https://typedrawers.com/discussion/2046/special-dash-things-softhyphen-horizontalbar
> 




> Original proposal: https://github.com/fonttools/fontbakery/issues/4046
> See also: https://github.com/fonttools/fontbakery/issues/3486





* ⚠️ **WARN** <p>This font has a 'Soft Hyphen' character.</p>
 [code: softhyphen]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Validate size, and resolution of article images, and ensure article page has minimum length and includes visual assets. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.html#googlefonts-article-images">googlefonts/article/images</a></summary>
    <div>


> 
> The purpose of this check is to ensure images (either raster or vector files)
> are not excessively large in filesize and resolution.
> 
> These constraints are loosely based on infrastructure limitations under
> default configurations.
> 
> It also ensures that the article page has a minimum length and includes
> at least one visual asset.
> 




> Original proposal: https://github.com/fonttools/fontbakery/issues/4594





* ⚠️ **WARN** <p>Family metadata at fonts/otf does not have an article.</p>
 [code: lacks-article]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Check for codepoints not covered by METADATA subsets. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.html#googlefonts-metadata-unreachable-subsetting">googlefonts/metadata/unreachable_subsetting</a></summary>
    <div>


> 
> This check ensures that all encoded glyphs in the font are covered by a
> subset declared in the METADATA.pb. Google Fonts splits the font into
> a set of subset fonts based on the contents of the `subsets` field and
> the subset definitions in the `glyphsets` repository.
> 
> Any encoded glyphs which are not by any of these subset definitions
> will not be served in the subsetted fonts, and so will be unreachable to
> the end user.
> 




> Original proposal: https://github.com/fonttools/fontbakery/issues/4097
> See also: https://github.com/fonttools/fontbakery/pull/4273





* ⚠️ **WARN** <p>The following codepoints supported by the font are not covered by
any subsets defined in the font's metadata file, and will never
be served. You can solve this by either manually adding additional
subset declarations to METADATA.pb, or by editing the glyphset
definitions.</p>
<ul>
<li>U+0009 : try adding symbols</li>
<li>U+000A : try adding symbols</li>
<li>U+0085 : try adding symbols</li>
<li>U+02D8 BREVE: try adding one of: canadian-aboriginal, yi</li>
<li>U+02D9 DOT ABOVE: try adding one of: canadian-aboriginal, yi</li>
<li>U+02DB OGONEK: try adding one of: canadian-aboriginal, yi</li>
<li>U+0302 COMBINING CIRCUMFLEX ACCENT: try adding one of: math, coptic, tifinagh, cherokee</li>
<li>U+0306 COMBINING BREVE: try adding one of: tifinagh, old-permic</li>
<li>U+0307 COMBINING DOT ABOVE: try adding one of: coptic, tai-le, old-permic, math, todhri, tifinagh, hebrew, syriac, canadian-aboriginal, duployan, malayalam</li>
<li>U+030A COMBINING RING ABOVE: try adding one of: duployan, syriac
314 more.</li>
</ul>
<p>Use -F or --full-lists to disable shortening of long lists.</p>
<p>Or you can add the above codepoints to one of the subsets supported by the font: <code>latin</code>, <code>latin-ext</code></p>
 [code: unreachable-subsetting]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Shapes languages in all GF glyphsets. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.html#googlefonts-glyphsets-shape-languages">googlefonts/glyphsets/shape_languages</a></summary>
    <div>


> 
> This check uses a heuristic to determine which GF glyphsets a font supports.
> Then it checks the font for correct shaping behaviour for all languages in
> those glyphsets.
> 




> Original proposal: https://github.com/googlefonts/fontbakery/issues/4147





* ⚠️ **WARN** <p>GF_TransLatin_Arabic glyphset:</p>
<table>
<thead>
<tr>
<th align="left">WARN messages</th>
<th align="left">Languages</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ǿ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ǿ</td>
<td align="left">da_Latn (Danish)</td>
</tr>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ſ</td>
<td align="left">de_Latn (German)</td>
</tr>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ʻ</td>
<td align="left">en_Latn (English)</td>
</tr>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ǧ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ǥ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ȟ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ǩ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ʒ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ǯ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ǧ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ǥ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ȟ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ǩ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ʒ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ǯ</td>
<td align="left">fi_Latn (Finnish)</td>
</tr>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ǔ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ſ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ǔ</td>
<td align="left">fr_Latn (French)</td>
</tr>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ẽ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ẽ</td>
<td align="left">lt_Latn (Lithuanian)</td>
</tr>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: Ǎ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ǎ</td>
<td align="left">nb_Latn (Norwegian Bokmål)</td>
</tr>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ڜ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ڢ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ڤ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ڥ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ٯ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ڧ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ڨ</td>
<td align="left">ar_Arab (Arabic)</td>
</tr>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ٖ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid233 to the base glyph when shaping the text '◌َ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid234 to the base glyph when shaping the text '◌ِ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid237 to the base glyph when shaping the text '◌ُ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid239 to the base glyph when shaping the text '◌ْ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid241 to the base glyph when shaping the text '◌ٰ'</td>
<td align="left">fa_Arab (Persian)</td>
</tr>
<tr>
<td align="left">Auxiliary orthography codepoints:</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ؀؁؂؃‌‍‏</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ٖ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ٗ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ٘</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ں</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ۂ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ۃ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ٻ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ٺ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ټ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">The following auxiliary characters are missing from the font: ٽ</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid235 to the base glyph when shaping the text '◌ً'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid238 to the base glyph when shaping the text '◌ٌ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid236 to the base glyph when shaping the text '◌ٍ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid233 to the base glyph when shaping the text '◌َ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid237 to the base glyph when shaping the text '◌ُ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid234 to the base glyph when shaping the text '◌ِ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid240 to the base glyph when shaping the text '◌ّ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid239 to the base glyph when shaping the text '◌ْ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid242 to the base glyph when shaping the text '◌ٔ'</td>
<td align="left"></td>
</tr>
<tr>
<td align="left">Shaper didn't attach gid241 to the base glyph when shaping the text '◌ٰ'</td>
<td align="left">ur_Arab (Urdu)</td>
</tr>
</tbody>
</table>
 [code: warning-language-shaping]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Ensure soft_dotted characters lose their dot when combined with marks that replace the dot. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.html#soft-dotted">soft_dotted</a></summary>
    <div>


> 
> An accent placed on characters with a "soft dot", like i or j, causes
> the dot to disappear.
> An explicit dot above can be added where required.
> See "Diacritics on i and j" in Section 7.1, "Latin" in The Unicode Standard.
> 
> Characters with the Soft_Dotted property are listed in
> https://www.unicode.org/Public/UCD/latest/ucd/PropList.txt
> 
> See also:
> https://googlefonts.github.io/gf-guide/diacritics.html#soft-dotted-glyphs
> 




> Original proposal: https://github.com/fonttools/fontbakery/issues/4059





* ⚠️ **WARN** <p>The dot of soft dotted characters used in orthographies <em>must</em> disappear in the following strings: į̀ į́ į̂ į̃ į̄ į̌</p>
<p>The dot of soft dotted characters <em>should</em> disappear in other cases, for example: i̦̇ i̦̊ i̦̋ ǐ̦ i̧̇ i̧̊ i̧̋ ǐ̧ j̦̀ j̦́ j̦̃ j̦̄ j̦̆ j̦̇ j̦̈ j̦̊ j̦̋ ǰ̦ j̧̀ j̧́</p>
 [code: soft-dotted]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Are there any misaligned on-curve points? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.html#outline-alignment-miss">outline_alignment_miss</a></summary>
    <div>


> 
> This check heuristically looks for on-curve points which are close to, but
> do not sit on, significant boundary coordinates. For example, a point which
> has a Y-coordinate of 1 or -1 might be a misplaced baseline point. As well as
> the baseline, here we also check for points near the x-height (but only for
> lowercase Latin letters), cap-height, ascender and descender Y coordinates.
> 
> Not all such misaligned curve points are a mistake, and sometimes the design
> may call for points in locations near the boundaries. As this check is liable
> to generate significant numbers of false positives, it will pass if there are
> more than 100 reported misalignments.
> 




> Original proposal: https://github.com/fonttools/fontbakery/pull/3088





* ⚠️ **WARN** <p>The following glyphs have on-curve points which have potentially incorrect y coordinates:</p>
<pre><code>* seen (U+FEB1): X=997.0,Y=1.0 (should be at baseline 0?)

* sheen (U+FEB5): X=997.0,Y=1.0 (should be at baseline 0?)

* waw (U+FEED): X=484.0,Y=-1.0 (should be at baseline 0?)

* wawhamza (U+FE85): X=484.0,Y=-1.0 (should be at baseline 0?)

* uni0051 (U+0051): X=402.0,Y=-2.0 (should be at baseline 0?)

* uni0074 (U+0074): X=263.0,Y=-2.0 (should be at baseline 0?)

* uni00C4 (U+00C4): X=443.0,Y=588.0 (should be at cap-height 586?)

* uni00C4 (U+00C4): X=354.0,Y=588.0 (should be at cap-height 586?)

* uni00C4 (U+00C4): X=282.0,Y=588.0 (should be at cap-height 586?)

* uni00C4 (U+00C4): X=193.0,Y=588.0 (should be at cap-height 586?)

* 44 more.
</code></pre>
<p>Use -F or --full-lists to disable shortening of long lists.</p>
 [code: found-misalignments]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Do any segments have colinear vectors? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.html#outline-colinear-vectors">outline_colinear_vectors</a></summary>
    <div>


> 
> This check looks for consecutive line segments which have the same angle. This
> normally happens if an outline point has been added by accident.
> 
> This check is not run for variable fonts, as they may legitimately have
> colinear vectors.
> 




> Original proposal: https://github.com/fonttools/fontbakery/pull/3088





* ⚠️ **WARN** <p>The following glyphs have colinear vectors:</p>
<pre><code>* ae.fina: L&lt;&lt;57.0,144.0&gt;--&lt;56.0,117.0&gt;&gt; -&gt; L&lt;&lt;56.0,117.0&gt;--&lt;56.0,108.0&gt;&gt;

* ae.fina: L&lt;&lt;57.0,197.0&gt;--&lt;57.0,144.0&gt;&gt; -&gt; L&lt;&lt;57.0,144.0&gt;--&lt;56.0,117.0&gt;&gt;

* ain.fina (U+FECA): L&lt;&lt;208.0,0.0&gt;--&lt;684.0,0.0&gt;&gt; -&gt; L&lt;&lt;684.0,0.0&gt;--&lt;708.0,0.0&gt;&gt;

* alef.fina (U+FE8E): L&lt;&lt;123.0,0.0&gt;--&lt;308.0,0.0&gt;&gt; -&gt; L&lt;&lt;308.0,0.0&gt;--&lt;332.0,0.0&gt;&gt;

* alefwasla.fina (U+FB51): L&lt;&lt;123.0,0.0&gt;--&lt;308.0,0.0&gt;&gt; -&gt; L&lt;&lt;308.0,0.0&gt;--&lt;332.0,0.0&gt;&gt;

* dad.fina (U+FEBE): L&lt;&lt;471.0,331.0&gt;--&lt;472.0,242.0&gt;&gt; -&gt; L&lt;&lt;472.0,242.0&gt;--&lt;472.0,-124.0&gt;&gt;

* dad.fina (U+FEBE): L&lt;&lt;471.0,352.0&gt;--&lt;471.0,331.0&gt;&gt; -&gt; L&lt;&lt;471.0,331.0&gt;--&lt;472.0,242.0&gt;&gt;

* dad.fina (U+FEBE): L&lt;&lt;622.0,226.0&gt;--&lt;735.0,242.0&gt;&gt; -&gt; L&lt;&lt;735.0,242.0&gt;--&lt;745.0,244.0&gt;&gt;

* dal.fina (U+FEAA): L&lt;&lt;56.0,0.0&gt;--&lt;608.0,0.0&gt;&gt; -&gt; L&lt;&lt;608.0,0.0&gt;--&lt;632.0,0.0&gt;&gt;

* ddal (U+0688): L&lt;&lt;192.0,484.0&gt;--&lt;192.0,483.0&gt;&gt; -&gt; L&lt;&lt;192.0,483.0&gt;--&lt;192.0,476.0&gt;&gt;

* 62 more.
</code></pre>
<p>Use -F or --full-lists to disable shortening of long lists.</p>
 [code: found-colinear-vectors]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Do outlines contain any semi-vertical or semi-horizontal lines? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.html#outline-semi-vertical">outline_semi_vertical</a></summary>
    <div>


> 
> This check detects line segments which are nearly, but not quite, exactly
> horizontal or vertical. Sometimes such lines are created by design, but often
> they are indicative of a design error.
> 
> This check is disabled for italic styles, which often contain nearly-upright
> lines.
> 




> Original proposal: https://github.com/fonttools/fontbakery/pull/3088





* ⚠️ **WARN** <p>The following glyphs have semi-vertical/semi-horizontal lines:</p>
<pre><code>* dad (U+FEBD): L&lt;&lt;471.0,370.0&gt;--&lt;472.0,-106.0&gt;&gt;

* gaf (U+FB92): L&lt;&lt;891.0,424.0&gt;--&lt;890.0,566.0&gt;&gt;

* gaf.fina (U+FB93): L&lt;&lt;891.0,424.0&gt;--&lt;890.0,566.0&gt;&gt;

* gaf.init (U+FB94): L&lt;&lt;639.0,424.0&gt;--&lt;638.0,566.0&gt;&gt;

* gaf.medi (U+FB95): L&lt;&lt;639.0,424.0&gt;--&lt;638.0,566.0&gt;&gt;

* jeh (U+FB8A): L&lt;&lt;245.0,364.0&gt;--&lt;246.0,0.0&gt;&gt;

* jeh.fina (U+FB8B): L&lt;&lt;245.0,364.0&gt;--&lt;246.0,0.0&gt;&gt;

* keheh (U+FED9): L&lt;&lt;891.0,424.0&gt;--&lt;890.0,566.0&gt;&gt;

* keheh.fina (U+FEDA): L&lt;&lt;891.0,424.0&gt;--&lt;890.0,566.0&gt;&gt;

* keheh.init (U+FEDB): L&lt;&lt;639.0,424.0&gt;--&lt;638.0,566.0&gt;&gt;

* 21 more.
</code></pre>
<p>Use -F or --full-lists to disable shortening of long lists.</p>
 [code: found-semi-vertical]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Ensure fonts have ScriptLangTags declared on the 'meta' table. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.html#googlefonts-meta-script-lang-tags">googlefonts/meta/script_lang_tags</a></summary>
    <div>


> 
> The OpenType 'meta' table originated at Apple. Microsoft added it to OT with
> just two DataMap records:
> 
> - dlng: comma-separated ScriptLangTags that indicate which scripts,
> or languages and scripts, with possible variants, the font is designed for.
> 
> - slng: comma-separated ScriptLangTags that indicate which scripts,
> or languages and scripts, with possible variants, the font supports.
> 
> 
> The slng structure is intended to describe which languages and scripts the
> font overall supports. For example, a Traditional Chinese font that also
> contains Latin characters, can indicate Hant,Latn, showing that it supports
> Hant, the Traditional Chinese variant of the Hani script, and it also
> supports the Latn script.
> 
> The dlng structure is far more interesting. A font may contain various glyphs,
> but only a particular subset of the glyphs may be truly "leading" in the design,
> while other glyphs may have been included for technical reasons. Such a
> Traditional Chinese font could only list Hant there, showing that it’s designed
> for Traditional Chinese, but the font would omit Latn, because the developers
> don’t think the font is really recommended for purely Latin-script use.
> 
> The tags used in the structures can comprise just script, or also language
> and script. For example, if a font has Bulgarian Cyrillic alternates in the
> locl feature for the cyrl BGR OT languagesystem, it could also indicate in
> dlng explicitly that it supports bul-Cyrl. (Note that the scripts and languages
> in meta use the ISO language and script codes, not the OpenType ones).
> 
> This check ensures that the font has the meta table containing the
> slng and dlng structures.
> 
> All families in the Google Fonts collection should contain the 'meta' table.
> Windows 10 already uses it when deciding on which fonts to fall back to.
> The Google Fonts API and also other environments could use the data for
> smarter filtering. Most importantly, those entries should be added
> to the Noto fonts.
> 
> In the font making process, some environments store this data in external
> files already. But the meta table provides a convenient way to store this
> inside the font file, so some tools may add the data, and unrelated tools
> may read this data. This makes the solution much more portable and universal.
> 




> Original proposal: https://github.com/fonttools/fontbakery/issues/3349





* ⚠️ **WARN** <p>This font file does not have a 'meta' table.</p>
 [code: lacks-meta-table]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Checking OS/2 achVendID. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.html#googlefonts-vendor-id">googlefonts/vendor_id</a></summary>
    <div>


> 
> Microsoft keeps a list of font vendors and their respective contact info. This
> list is updated regularly and is indexed by a 4-char "Vendor ID" which is
> stored in the achVendID field of the OS/2 table.
> 
> Registering your ID is not mandatory, but it is a good practice since some
> applications may display the type designer / type foundry contact info on some
> dialog and also because that info will be visible on Microsoft's website:
> 
> https://docs.microsoft.com/en-us/typography/vendors/
> 
> This check verifies whether or not a given font's vendor ID is registered in
> that list or if it has some of the default values used by the most common
> font editors.
> 
> Each new FontBakery release includes a cached copy of that list of vendor IDs.
> If you registered recently, you're safe to ignore warnings emitted by this
> check, since your ID will soon be included in one of our upcoming releases.
> 




> Original proposal: https://github.com/fonttools/fontbakery/issues/3943
> See also: https://github.com/fonttools/fontbakery/issues/4829





* ⚠️ **WARN** <p>OS/2 VendorID value 'AZRS' is not yet recognized. If you registered it recently, then it's safe to ignore this warning message. Otherwise, you should set it to your own unique 4 character code, and register it with Microsoft at <a href="https://www.microsoft.com/typography/links/vendorlist.aspx">https://www.microsoft.com/typography/links/vendorlist.aspx</a></p>
 [code: unknown]



</div>
</details>
</div>
</details>




### Summary

| 💥 ERROR | ☠ FATAL | 🔥 FAIL | ⚠️ WARN | ⏩ SKIP | ℹ️ INFO | ✅ PASS | 🔎 DEBUG | 
| ---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 12 | 125 | 5 | 94 | 0 | 
| 0% | 0% | 0% | 5% | 53% | 2% | 40% | 0% | 



**Note:** The following loglevels were omitted in this report:


* SKIP
* INFO
* PASS
* DEBUG
