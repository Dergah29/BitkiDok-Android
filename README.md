# BitkiDok — working web app foundation

Four languages: English, German, Russian and Turkish. Mobile layout, camera/gallery upload, local plant collection, soil-check due list, photo resizing, JSON export. No fake analysis or billing.

## Run

Requires Node.js 20+. Run `npm start` in this directory and open `http://localhost:3000`.

To enable real photo analysis, set `PLANT_ID_API_KEY` as a **server environment variable** before starting. The app calls Kindwise Plant.id v3 through the server. Never put the key in a web page or commit it. The provider charges per request and currently offers optional health assessment. The server limits requests per IP, but public deployment needs account based quotas, authentication, monitoring, abuse protection and costs controls.

Photo analysis has not been live tested because no API key was supplied. Provider response fields and localized plant details need live validation. Health suggestions are uncertain; the app deliberately avoids chemical treatment prescriptions.

## What is still required for release

- Android/iOS native notification delivery. Current soil reminders appear only inside the open app. Browser background alerts are not implemented.
- Account and secure cloud sync, with consent and privacy policy for uploaded photos.
- Paid plan implementation through the relevant store billing SDK; Plus is currently an informational screen.
- User testing of the image service, its care fields and translated output with real plants.
- App store assets, accessibility QA, publishing and device testing.

The plant list is stored in browser localStorage. Clearing browser data removes it; Export downloads a backup.

## GitHub və Google Play vəziyyəti

Bu repo hazırda Node.js veb prototipidir, Android APK/AAB deyil. GitHub Actions yalnız sintaksis və serverin açılmasını yoxlayır; Android paketi yaratmır. Google Play-ə göndərməzdən əvvəl Android tətbiqi, HTTPS ilə işləyən backend, məxfi açarın serverdə saxlanması, canlı şəkil analizi sınağı, ödəniş inteqrasiyası, məxfilik məlumatları və buraxılış paketi hazırlanmalıdır. `PLANT_ID_API_KEY` heç vaxt repoya və mobil APK-yə əlavə edilməməlidir.

## Offline qulluq bazası – ilkin mərhələ

`public/offline.js` 8 ev bitkisi üçün növ seçimi, torpaq/işıq/belirti qaydaları və EN/DE/RU/TR mətnlərini saxlayır. Scan səhifəsinin aşağısındakı bələdçi API açarı olmadan işləyir. Bu, şəkil tanıma modeli deyil: istifadəçi əlamətləri özü seçir, nəticə mümkün səbəbdir. Zəhərli/kimyəvi vasitə və təsdiqlənmiş xəstəlik diaqnozu verilmir. Hər növ və problem üçün lisenziyası uyğun şəkillər, ayrıca təsdiq edilmiş etiketlər və real foto testləri əldə olunmadan bu məlumatla şəkil modelini öyrətmək olmaz.

## Image recognition training scaffold

`ml/` contains a licensed-photo manifest validator and an experimental TensorFlow MobileNetV2 trainer that exports a LiteRT/TFLite species model. An experimental model trained on 787 original licensed photos is available from [the successful training run](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35104625186) as the `bitkidok-experimental-model` artifact (model.tflite, labels.json, metrics.json). It covers just 9 health/condition classes for money plant, snake plant, and spider plant. Its held-out split accuracy was 92.99%, but an independent real-world test has not been done; unseen plants and conditions can receive misleading confident predictions. To try a photo locally, download and unzip the artifact, install `tensorflow` and `pillow`, and run `python ml/predict.py photo.jpg artifact-folder`. This does not connect the model to the web scanner or provide a Google Play app. The scanner still uses Kindwise when configured. See `ml/README.md`.


## Android foto sınağı (eksperimental)

`android/` cihazda işləyən ayrıca Java/TFLite sınaq tətbiqidir. `Android debug APK` GitHub Actions işi əvvəlki model təliminin artifact-ini yükləyib APK daxilinə qoyur, sonra `BitkiDok-debug-apk` artifact-i yaradır. APK test məqsədlidir, Play Store buraxılışı deyil. Android Studio-da lokal build üçün model artifact-ini açıb `model.tflite` faylını `android/app/src/main/assets/` qovluğuna köçürmək lazımdır. Ekranda kamera və qalereyadan şəkil seçimi var; foto telefonun içində təhlil olunur, API krediti istifadə edilmir. Model yalnız pothos, sansevieria və spider plant üçün 9 vəziyyəti tanımağa çalışır. Naməlum bitki və ya vəziyyəti inkar edə bilmir; nəticə yanlış ola bilər. Hazırkı Android sınağında bitki kolleksiyası, xatırlatmalar, dörd dil və ödəniş sistemi yoxdur; onlar veb prototipindəki funksiyalardan ayrıca Android tətbiqinə daşınmalıdır.


### Genişləndirilmiş növ tanıma sınağı (17 sentyabr 2026)

[10 növlük növ modeli təlimi](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35196157117) və [Android APK build-i](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35197113740) uğurla tamamlandı. Foto ekranı 10 növdən birinin Latın adını təklif edir: aloe vera, chlorophytum comosum, crassula ovata, epipremnum aureum, ficus benjamina, ficus elastica, monstera deliciosa, schlumbergera truncata, spathiphyllum wallisii və tradescantia zebrina. Dataset daxilində ayrılmış yoxlama nəticəsi **62,1%** oldu (482 foto, 10 növ); bu, real telefon fotolarında keyfiyyətə zəmanət deyil. Model naməlum növləri rədd etmək üçün ayrıca öyrədilməyib. Ekran aşağı göstəricidə qeyri-müəyyənlik bildirir, lakin daha yüksək göstərici də düzgünlük zəmanəti vermir. Yalnız növ tanıma ekrana qoşulub; xəstəlik və qulluq məsləhətləri bu Android ekranında avtomatik diaqnoz kimi göstərilmir. Yayımlamadan əvvəl daha böyük, ayrıca test dəsti və real cihaz sınağı lazımdır. Təlim şəkillərinin mənbə və müəllif qeydləri model artifact-ində `attribution.json` içindədir; [GBIF-in istifadə və istinad qaydalarına](https://techdocs.gbif.org/en/data-use/citation) əməl olunmalıdır.


### Daha çox növ (daxili sınaq)

[İkinci təlimdə](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35203022732) lisenziyası ayrıca yoxlanmış GBIF fotoları əsasında 21 növlük eksperimental model yaradıldı. Ayrılmış eyni mənbəli şəkillərdə ilk seçim dəqiqliyi 58,0% oldu; naməlum növləri rədd etməyi bilmir. [Android build](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35204043013) model və etiketləri APK-yə daxil edir, ekranda ilk üç təxmini göstərir. Növlərin tam siyahısı `bitkidok-species-experimental` artifact-ində `species-labels.json` içindədir; istifadə olunan şəkillərin müəllif, mənbə və lisenziyası `attribution.json`-dadır. Bu keyfiyyət istehlakçıya dəqiq tanıma vəd etmək üçün kifayət deyil; ayrıca real foto sınağı və daha çox düzgün etiketli data lazımdır. API abunəliyi foto datasetinin mülkiyyət/lisenziyasını vermir, ona görə dataset alışı yalnız yazılı model təlimi və kommersiya istifadə hüquqları aydın olanda nəzərdən keçirilməlidir.


### 200 ev bitkisi kataloqu

[`data/houseplants_200.json`](data/houseplants_200.json) faylında 200 ayrı botaniki qeyd və GBIF taxon açarı var. Siyahı 245 namizəddən [GBIF ad yoxlaması](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35206411921) ilə seçilib; 21 qeyd hazırkı eksperimental foto modelinə daxildir, 179 qeyd hələ yalnız kataloq namizədidir. Növlərin evdə saxlanması, satış adları, qulluq məlumatları və şəkil tanıma keyfiyyəti ayrıca redaktə və sınaq tələb edir. Kataloq əlavə edilməsi APK-nin 200 növü fotodan tanıması demək deyil.

### 200 bitki üçün qulluq kartları (ilkin redaktə)

[`data/houseplants_200_details_az.json`](data/houseplants_200_details_az.json) kataloqdakı 200 taxon açarının hər biri üçün Azərbaycan dilində işıq, suvarma, torpaq və otaq şəraiti üzrə **qrup səviyyəli ilkin bələdçi** saxlayır. 14 qulluq profili var; bunlar növ üzrə təsdiqlənmiş 200 fərdi qulluq təlimatı deyil. Suvarma sabit gün sayına deyil, torpağın vəziyyətinə əsaslanır. Ümumi metod üçün [RHS houseplant guide](https://www.rhs.org.uk/plants/types/houseplants/growing-guide) və [NC State Cooperative Extension](https://caldwell.ces.ncsu.edu/2021/01/indoor-plant-care-101/) göstərilib. Növə xas redaktə və ekspert yoxlaması yayım öncəsi lazımdır.

Mənşə/habitat sahələrində yalnız *Monstera deliciosa* üçün [Kew POWO](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:87478-1) əsasında təsdiqli məlumat var. Qalan 199 qeyddə mənşə və təbii yaşayış yeri `null` və `pending_species_verification` kimi saxlanır: ad və ya GBIF müşahidələrinə əsaslanıb ölkə təxmin edilmir. Bu məlumat hələ Android ekranında göstərilmir. [`data/houseplants_200_details_i18n.json`](data/houseplants_200_details_i18n.json) faylında 200 qeyd üçün ingilis, alman, rus və türk dillərində qrup səviyyəli qulluq mətnləri əlavə edilib. Azərbaycan dili ilə birlikdə beş dildə məlumat faylı var; Android tətbiqinə qoşulması, dil seçimi və tərcümələrin redaktə yoxlaması qalır. 200 qeydin yalnız 21-i eksperimental foto modelində var.

### 200 növü fotodan tanıma mərhələsi

[`ml/audit_200_coverage.py`](ml/audit_200_coverage.py) və [coverage workflow](.github/workflows/audit-200-coverage.yml) kataloqdakı 200 takson üzrə GBIF-də açıq lisenziyalı şəkil namizədlərini yoxlayır. Audit yalnız metadata sayır; şəkillərin işlək olması, düzgün etiket, müxtəlif şəraitdə çəkilməsi və modelin keyfiyyəti ayrıca yoxlanmalıdır. 200 siniflik model **hələ yaradılmayıb** və Android-in foto ekranı hələ 21 siniflik eksperimental modeldən istifadə edir. Audit nəticəsində şəkil çatışmayan növlər üçün uyğun lisenziyalı yeni foto toplamaq, məlumatları müstəqil bitki/foto üzrə bölmək, naməlum bitkiləri ayrıca sınaqdan keçirmək və sonra real cihazda yoxlamaq lazımdır. Yalnız kataloqun adlarını model etiketlərinə yazmaq foto tanıma yaratmır.

### 200 növ üçün geniş təlim sınağı

[GitHub Actions təlim işi](.github/workflows/train-catalog-species.yml) `data/houseplants_200.json` siyahısının hamısında lisenziyalı müşahidə fotolarını yoxlayır və `ml/prepare_200_species.py` ilə yükləyə bildiyi növlərdən eksperimental model öyrədir. Hər növ üçün ən az 12 fərqli GBIF müşahidəsinin işlək fotosu lazımdır; çatışmayanlar `coverage.json` hesabatında göstərilir. İlk [təlim işi](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35220856624) tamamlandı: **101 sinif**, 1925 təlim və 489 ayrılmış yoxlama fotosu, yoxlamada **40,49%** dəqiqlik. `coverage.json`, `species-labels.json`, `species-metrics.json`, `attribution.json` və `species.tflite` işin artifact-indədir. Bu bölmə eyni GBIF mənbəli təsadüfi ayrımdır, müstəqil telefon fotosu testi deyil. Hazırkı keyfiyyətlə modeli istehlakçıya dəqiq 200 növ tanıma kimi təqdim etmək olmaz. Model 200 siniflə nəticələnməyə bilər; 200 sinifin hamısı uğurla yığılıb öyrədilmədən '200 növ tanıyır' yazılmamalıdır. Bu sınağın modeli Android APK-yə avtomatik yerləşdirilmir; ayrıca keyfiyyət və cihaz testi lazımdır.

### Daha dərin foto axtarışı və ikinci model

[İkinci təlim](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35224203639) eyni 101 növ üzrə 1925 təlim və 489 yoxlama fotosu ilə aparıldı; ayrılmış fotolarda top-1 **34,56%**, top-3 **53,17%** oldu. Bu, əvvəlki 40,49% top-1 nəticəsindən aşağıdır, ona görə APK-yə keçirilməyib. [Daha dərin GBIF axtarışı](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35226993243) əvvəllər az foto tapılan 99 növün 49-unda cəmi 407 əlavə URL namizədi gördü; [`data/gbif_deep_coverage_99.json`](data/gbif_deep_coverage_99.json) nəticələri saxlayır. Bunlar hələ yüklənmiş və düzgün etiketlənmiş fotolar deyil, əvvəlki fotolarla üst-üstə düşə bilər. Növbəti təlimdə URL-lər yoxlanmalı, dublikatlar çıxarılmalı və təlim/yoxlama fotoları bitki fərdi üzrə ayrılmalıdır.

### Dərin səhifələrdən foto yığımı nəticəsi

[Üçüncü təlim](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35232494487) GBIF-in sonrakı səhifələrini də yoxladı, amma yüklənmiş işlək foto sayları bütün 200 növ üzrə əvvəlki cəhdlə tam eyni qaldı: 101 model sinfi, 1925 təlim və 489 yoxlama fotosu. Top-1 **34,15%**, top-3 **51,33%** oldu. `data/gbif_deeper_training_result.json` nəticəni saxlayır. Əlavə URL namizədləri doğrulanmış yeni şəkillərə çevrilmədiyi üçün hazırki mənbəni təkrar sorğulamaqla 200 sinfə çıxmaq mümkün olmayıb; yeni hüququ uyğun, növü yoxlanmış foto mənbələri və müstəqil telefon fotosu testi lazımdır. Bu model Android-ə qoşulmayıb.

### iNaturalist alternativ foto auditi (17 sentyabr 2026)

[iNaturalist audit işi](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35248530891) əvvəlki GBIF təlimində foto sayı 12-dən az olan 99 növü dəqiq latın adına və hər foto üçün CC0/CC BY metadata lisenziyasına görə yoxladı. [Növ üzrə xülasə](data/inat_coverage_99_summary.json) və [428 namizədin mənbə/foto ID manifesti](data/inat_photo_candidates_99.json) repodadır: 46 növdə cəmi 428 namizəd (326 CC BY, 102 CC0), 53 növdə namizəd yoxdur. Yalnız bütün fotoları yararlı fərz etsək, 17 növ əvvəlki fotolarla birlikdə 12-lik həddə çata *bilər*; bu faktiki model sinfi deyil. Əvvəlki GBIF təliminin 2384 iNaturalist foto ID-si ilə bu 428 ID-nin birbaşa kəsişməsi sıfırdır; vizual dublikat və səhv etiket yenə mümkün ola bilər. API çox vaxt 75px `square` URL verir, buna görə [ayrıca orta ölçülü fotonun yüklənmə/dekodlanma yoxlaması](.github/workflows/validate-inat-photos.yml) lazımdır. Təkcə lisenziya metadata-sı etiketin düzgünlüyünü, fotonun istifadəyə tam hüquqi yararlılığını və real telefon keyfiyyətini təmin etmir. Model hələ 101 sinifdir, top-1 34,15%, top-3 51,33%; APK-yə yeni model qoşulmayıb. Mənbə: [iNaturalist lisenziya və istifadə qaydaları](https://www.inaturalist.org/pages/terms), [iNaturalist Open Data foto atribusiya qaydaları](https://github.com/inaturalist/inaturalist-open-data).

### iNaturalist orta ölçülü foto doğrulaması

[17 sentyabr 2026 yükləmə yoxlaması](https://github.com/Dergah29/BitkiDok-Android/actions/runs/35255435922) 428 metadata namizədindən **189** fotonu orta ölçüdə yükləyib açdı və bu namizəd partiyasında SHA-256 üzrə təkrar baytları rədd etdi. Şəkillər 99 çatışmayan növün 43-nə aiddir. [Növ üzrə texniki yoxlama hesabatı](data/inat_download_validation_99.json) göstərir ki, nəzəri olaraq əvvəlki GBIF fotoları ilə cəmlədikdə 15 növ 12 müşahidə həddinə çata bilər. Amma iki mənbə arasında vizual/fərdi dublikat, növ etiketi və foto hüquqları ayrıca yoxlanmayıb; bu fotolar **təlimə qəbul edilməyib**, model hələ **101 sinif**, top-1 **34,15%**, top-3 **51,33%**-dir. Müstəqil telefon foto testi yoxdur.
