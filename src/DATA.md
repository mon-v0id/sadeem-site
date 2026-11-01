# Sadeem Open Data

Sadeem's reference table, used to add your own objects to the app, is built
from two open catalogues published under the **Creative Commons
Attribution-ShareAlike 4.0 International** licence (CC BY-SA 4.0):

- **OpenNGC** by Mattia Verga — <https://github.com/mattiaverga/OpenNGC>
- **HYG Stellar Database 4.4** by David Nash (astronexus) —
  <https://codeberg.org/astronexus/hyg>

Our adapted table is available here **under the same licence, CC BY-SA 4.0**.
You may share and adapt it, including commercially, as long as you credit the
original authors and Sadeem, and share your adaptations under the same
licence.

## Files

- [reference-objects.json](/data/reference-objects.json) — the adapted table
  (CC BY-SA 4.0)
- [LICENSE-CC-BY-SA-4.0.txt](/data/LICENSE-CC-BY-SA-4.0.txt) — the full licence
- [reference_tables.py](/data/reference_tables.py) — the script that builds
  the table, published so the changes can be seen (MIT licence)

## What we changed

The table converts both catalogues into one compact file and trims them:

- stars come from HYG: every star brighter than magnitude 6.5 and every star
  with a proper name;
- deep-sky objects come from OpenNGC; its star, asterism, association,
  duplicate, group, non-existent and nova entries are left out, and
  duplicates become aliases of the object they repeat;
- coordinates are converted to decimal degrees, and each row records which of
  Sadeem's own objects it is, if any.

Attribution: "Contains data from OpenNGC by Mattia Verga and the HYG Stellar
Database by David Nash, adapted by Sadeem, CC BY-SA 4.0."

This licence applies only to the files on this page. The rest of Sadeem — its
software, text, lessons, illustrations and design — is not covered by it; see
the [Terms of Use](/terms/).
