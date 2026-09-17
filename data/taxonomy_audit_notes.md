# Taxonomy audit of the 200 catalog entries

Audited 2026-09-17 UTC via [full GBIF workflow](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35268209829). Full [200-record JSON report](catalog_taxonomy_audit_200.json); earlier [31 unmatched-name report](taxon_alias_audit_31.json). These are taxonomy metadata checks, **not** photo-label reviews or model evaluation.

| Measure | Result |
| --- | ---: |
| Catalog entries / distinct queried GBIF keys | 200 / 200 |
| GBIF keys successfully resolved | 200 |
| GBIF record ranks reported as SPECIES | 200 |
| GBIF ACCEPTED / SYNONYM statuses | 183 / 17 |
| Distinct resolved accepted GBIF keys | **197** |

Three pairs share one accepted GBIF key each:

| Catalog entries | Accepted GBIF key | Review note |
| --- | ---: | --- |
| Asparagus setaceus / Asparagus plumosus | 2768686 | GBIF lists plumosus as a synonym of setaceus. |
| Begonia maculata / Begonia corallina | 7303475 | GBIF lists corallina as a synonym of maculata. |
| Hoya carnosa / Hoya compacta | 8658195 | GBIF lists compacta as a synonym of carnosa; a recognizable horticultural form may still deserve a distinct user-facing name, but not a second accepted species count. |

The 200 queried records have species rank; a synonym can resolve to an accepted infraspecific taxon (for example Philodendron micans and Saintpaulia ionantha in the 31-name report). Thus **197 distinct accepted keys does not itself prove 197 accepted species at species rank**. Before claiming 200 accepted species, inspect ranks of all accepted targets and select botanically verified replacements for duplicated or infraspecific entries. Do not silently merge labels or include a source photograph under a different label based only on iNaturalist autocomplete.

The 31-name audit found 15 GBIF synonyms and 16 accepted entries among exact-name iNaturalist misses. Autocomplete suggestions are not synonym evidence; notably Dieffenbachia amoena / Dieffenbachia seguine cannot be merged on that basis.

The experimental photo model still has 101 labels and same-source top-1 34.15% / top-3 51.33%. Photos from additional sources require image-level rights, taxon, visual and duplicate checks, then independent phone-photo evaluation. None of these taxonomy counts implies a trained 197- or 200-class model.
