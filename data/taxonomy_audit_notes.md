# Taxonomy audit: 31 names missed by iNaturalist exact search

Audit date: 2026-09-17 UTC. [GitHub Actions run](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35267693772), [machine-readable results](taxon_alias_audit_31.json). This is a taxonomy metadata audit, **not photo label validation or model training**.

The catalog currently has 200 entries with 200 different GBIF taxon keys, but these are not proven to be 200 different accepted species. Of the 31 catalog names that had no unambiguous exact species match in the iNaturalist photo audit, GBIF marks 15 as synonyms and 16 as accepted entries. iNaturalist autocomplete suggestions have not been verified as synonym relationships.

At least two catalog pairs resolve to the same GBIF accepted taxon:

| Catalog label A | GBIF accepted key | Existing catalog label B | Interpretation |
| --- | ---: | --- | --- |
| Asparagus plumosus | 2768686 | Asparagus setaceus | GBIF synonym of same accepted taxon; do not count as two botanical species. |
| Hoya compacta | 8658195 | Hoya carnosa | GBIF synonym of same accepted taxon; compacta may be a distinct horticultural form, but do not count as a second accepted species. |

Examples requiring label review before a photo search under the iNaturalist name: Dracaena trifasciata / Sansevieria trifasciata, Philodendron bipinnatifidum / Thaumatophyllum bipinnatifidum, Senecio rowleyanus / Curio rowleyanus. A search suggestion alone is insufficient evidence for an automatic alias. In particular, Dieffenbachia amoena / Dieffenbachia seguine should **not** be merged on autocomplete similarity.

Next gates: audit all 200 GBIF keys for accepted-taxon duplicates and ranks; botanically verify names; replace duplicate catalog entries with genuinely distinct species if the requirement is 200 species; license-check each photograph, verify its taxon and duplicates, then train and test on independent phone photos. The experimental model remains 101 labels, top-1 34.15% and top-3 51.33% on the earlier same-source validation; no independent phone-photo accuracy has been established. No model or app-release claim follows from this taxonomy report.
