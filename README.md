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

Mənşə/habitat sahələrində yalnız *Monstera deliciosa* üçün [Kew POWO](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:87478-1) əsasında təsdiqli məlumat var. Qalan 199 qeyddə mənşə və təbii yaşayış yeri `null` və `pending_species_verification` kimi saxlanır: ad və ya GBIF müşahidələrinə əsaslanıb ölkə təxmin edilmir. Bu məlumat faylı hələ Android ekranında göstərilmir; tətbiqə qoşulması və dörd dilə tərcüməsi növbəti işdir. 200 qeydin yalnız 21-i eksperimental foto modelində var.
