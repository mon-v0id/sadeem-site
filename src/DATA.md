# Sadeem Open Data

Sadeem's reference table, used to add your own objects to the app, is built
from two open catalogues published under the **Creative Commons
Attribution-ShareAlike 4.0 International** licence (CC BY-SA 4.0):

- **OpenNGC** by Mattia Verga — <https://github.com/mattiaverga/OpenNGC>
- **HYG Stellar Database 4.4** by David Nash (astronexus) —
  <https://codeberg.org/astronexus/hyg>

Beside the table, the free Sky Map uses **deep-stars.bin**: the stars of the
HYG Stellar Database 4.4 by David Nash (astronexus) from magnitude 6.5 to 9
that are not in the table, shown as you zoom in. It is adapted from HYG, which
is licensed CC BY-SA 4.0 (<https://creativecommons.org/licenses/by-sa/4.0/>).

Our adapted table and our adapted deep-stars.bin are available here **under
the same licence, CC BY-SA 4.0**. You may share and adapt them, including
commercially, as long as you credit the original authors and Sadeem, and share
your adaptations under the same licence.

## Files

- [reference-objects.json](/data/reference-objects.json) — the adapted table
  (CC BY-SA 4.0)
- [deep-stars.bin](/data/deep-stars.bin) — HYG stars from magnitude 6.5 to 9
  not in the table above, packed as binary records (layout in
  reference_tables.py, deep_star_bytes); adapted by Sadeem, CC BY-SA 4.0
- [LICENSE-CC-BY-SA-4.0.txt](/data/LICENSE-CC-BY-SA-4.0.txt) — the full licence
- [reference_tables.py](/data/reference_tables.py) — the script that builds
  the table and deep-stars.bin, published so the changes can be seen (MIT
  licence)

## What we changed

The table converts both catalogues into one compact file and trims them:

- stars come from HYG: every star brighter than magnitude 6.5 and every star
  with a proper name;
- each star also carries HYG's B−V colour index (the ci column), used to tint
  it on the map;
- deep-sky objects come from OpenNGC; its star, asterism, association,
  duplicate, group, non-existent and nova entries are left out, and
  duplicates become aliases of the object they repeat;
- coordinates are converted to decimal degrees, and each row records which of
  Sadeem's own objects it is, if any.

deep-stars.bin keeps only HYG's stars fainter than magnitude 6.5, down to 9,
that have no proper name, and only four things for each, in ten bytes: right
ascension and declination in degrees (little-endian 32-bit floats), the
magnitude above 6.5 in hundredths (one unsigned byte), and the B−V colour index
in fiftieths (one signed byte, −128 where it is unknown).

Attribution: "Contains data from OpenNGC by Mattia Verga and the HYG Stellar
Database by David Nash, adapted by Sadeem, CC BY-SA 4.0."

This licence applies only to the files on this page. The rest of Sadeem — its
software, text, lessons, illustrations and design — is not covered by it; see
the [Terms of Use](/terms/).
