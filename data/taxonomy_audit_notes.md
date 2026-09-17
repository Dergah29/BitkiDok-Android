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

The [accepted-rank check](accepted_rank_audit_200.json) resolved all 17 synonym targets and classified the **197 distinct accepted GBIF keys** as **193 SPECIES, 2 VARIETY, and 2 SUBSPECIES**. The four catalog entries pointing to accepted subspecific taxa are Philodendron micans (variety), Gasteria verrucosa (variety), Mammillaria gracilis (subspecies), and Saintpaulia ionantha (subspecies). Therefore only **193 accepted species-ranked taxa** are represented by the current 200-entry catalog under this GBIF backbone. Horticultural hybrids and alternative taxonomy may need further review. Seven additional distinct, accepted species-ranked taxa would be needed to claim 200 accepted species, with image rights, labels and coverage validated separately. Do not silently merge labels or include a source photograph under a different label based only on iNaturalist autocomplete.

The 31-name audit found 15 GBIF synonyms and 16 accepted entries among exact-name iNaturalist misses. Autocomplete suggestions are not synonym evidence; notably Dieffenbachia amoena / Dieffenbachia seguine cannot be merged on that basis.

The experimental photo model still has 101 labels and same-source top-1 34.15% / top-3 51.33%. Photos from additional sources require image-level rights, taxon, visual and duplicate checks, then independent phone-photo evaluation. None of these taxonomy counts implies a trained 197- or 200-class model.

## Replacement-name leads (2026-09-17 UTC)

[Reproducible 11-candidate metadata audit](replacement_taxa_candidates_11.json) ([workflow](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35278758890)) found 11 not-yet-cataloged accepted GBIF species-ranked keys, none equal to the 197 accepted keys above. Ten have an exact species-name iNaturalist autocomplete result; Calathea warscewiczii matches GBIF's accepted Goeppertia warscewiczii but has no exact iNaturalist autocomplete result under the old name. Five candidates have at least 100 iNaturalist observations by autocomplete count (Alocasia micholitziana, Pilea mollis, Dischidia nummularia, Hoya lacunosa, Monstera pinnatipartita). These counts **do not** indicate any number of CC0/CC BY photographs or validated houseplant images. No candidate has yet been added to the production catalog; next verify individual photo licenses and coverage, identity, deduplication, and horticultural suitability. Even a corrected list of 200 accepted species would not create a 200-class trained photo model.

## Replacement-photo metadata audit

[Photo-level CC0/CC BY candidate report](replacement_photo_candidates_11.json) ([workflow](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35278962551)) found 220 metadata photo candidates across 5 of the 11 names. The distribution is Dischidia nummularia 131, Monstera pinnatipartita 78, Alocasia micholitziana 4, Pilea mollis 4, Hoya lacunosa 3; the other six had no matching photos in this limited two-page research-grade iNaturalist query (Calathea under its synonym lacked an exact taxon match). Thus only **two** of the 11 currently reach the provisional 12-photo threshold in metadata. A photo can be unusable despite the license code; downloading, decoding, botanical label inspection and cross-source duplicate review are pending. Do not count these candidates as trained model classes or infer that seven replacements have enough usable photos.
