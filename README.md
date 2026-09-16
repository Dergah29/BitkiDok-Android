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
