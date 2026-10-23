# Napp — приложения, документы и поддержка

Общий статический сайт разработчика для GitHub Pages: https://napp-dev.github.io/.
Первое приложение — «Книга рецептов» / Recipe Book / Rezeptbuch / Książka kucharska.
Языки «Книги рецептов» и её документов: `en`, `ru`, `de`, `pl`.
Weekwall — календарь на экране блокировки iPhone: `en`, `ru`, `de`, `fr`, `es`, `es-419`, `pt-BR`, `it`, `ja`, `ko`.

## Навигация и постоянные адреса

- `/` — каталог приложений.
- `/apps/nyrecipes/` — выбор языка приложения.
- `/apps/nyrecipes/<язык>/` — описание, App Store, документы и поддержка.
- `/apps/nyrecipes/<язык>/privacy/` — политика конфиденциальности.
- `/apps/nyrecipes/<язык>/terms/` — условия использования.
- `/apps/nyrecipes/<язык>/support/` — поддержка.
- `/apps/weekwall/` — выбор языка Weekwall; структура описания и документов такая же, как у `nyrecipes`.
- `/app-ads.txt` — общий файл рекламных продавцов в корне домена.

Переключатель языка на документе открывает тот же вид документа на выбранном языке.
Страницы доступны напрямую без JavaScript, авторизации и автоматического перенаправления.
Коды приложений, языков и адреса документов после публикации не переименовывать: они будут использоваться в приложениях и App Store Connect.
Существующие сайты `/mortgageCalculator/` и `/ProofShot/` этим репозиторием не переносятся.

## Исходники и сборка

- `site.json` — бренд, адрес сайта, почта поддержки и список приложений в порядке каталога.
- `apps/<app-id>/app.json` — App Store, изображения, дата редакции и переводы интерфейса сайта.
- `content/<app-id>/<язык>/{privacy,terms,support}.md` — исходные тексты документов.
- `assets/style.css` — адаптивное оформление со светлой и тёмной темой.
- `assets/<app-id>/` — изображения приложения.
- `scripts/build_pages.py` — генератор без внешних зависимостей; Python 3.9+.
- `index.html`, `apps/**/index.html`, `404.html`, `sitemap.xml`, `robots.txt` — результат сборки. Вручную не редактируются.

Из корня репозитория:

```sh
python3 scripts/build_pages.py
python3 scripts/build_pages.py --check
python3 -m http.server 8914 --bind 127.0.0.1
```

Локальный просмотр: http://127.0.0.1:8914/. Открытие HTML через `file://` не подходит из-за ссылок от корня сайта.
Проверка валидирует все генерируемые страницы, локальные ссылки, якоря, языки, заголовки и актуальность результата сборки. GitHub Actions запускает её на push и pull request.
Markdown поддерживает один заголовок `#`, разделы `##`, абзацы, простые списки, HTTPS/mailto/локальные ссылки и `**жирный**`. HTML, таблицы и блоки кода в документах не поддерживаются.
В тексте документа доступны подстановки `{{app_name}}` и `{{contact_email}}`.

## Обновление документов

1. Менять текст на всех языках затронутого приложения с одинаковым смыслом. Для Weekwall английский — источник остальных переводов.
2. Обновить `updated` в `apps/<app-id>/app.json` (ISO `YYYY-MM-DD`).
3. Собрать сайт, выполнить `--check`, проверить изменённую страницу в браузере.
4. Сохранить исходники и готовый HTML одним коммитом.
5. После публикации проверить прямые ссылки и `/app-ads.txt`.

Новая редакция остаётся по тому же адресу. История изменений хранится в Git.
Состав данных сверяется с кодом приложения и SDK; Privacy Manifest сам по себе не заменяет политику.
В текстах описаны локальное хранилище, события меню (включая пищевые ограничения), Firebase Analytics/Crashlytics/Remote Config, AdMob, Yandex Mobile Ads с AppMetrica, ATT/UMP, покупки и поддержка.
Срок хранения Analytics в политике — 14 месяцев, как в консоли Google Analytics (Admin → Data retention); если срок в консоли изменится, обновите его во всех переводах.
Условия дополняют стандартную EULA Apple; отдельное пользовательское лицензионное соглашение в App Store Connect этими страницами не назначается.

## Добавление приложения

1. Выбрать постоянный `app-id` и добавить его в `site.json` → `apps`.
2. Создать `apps/<app-id>/app.json` по образцу `nyrecipes`: те же ключи локалей, свои названия, ссылки, даты, описания и изображения. Английский (`en`) — обязательная запасная локаль.
3. Подготовить три Markdown-документа для каждой объявленной локали в `content/<app-id>/<язык>/`.
4. Добавить изображения в `assets/<app-id>/` и запустить сборку.

Каталог, страницы выбора языка, навигация, sitemap и документы появятся из конфигурации.
Не копируйте политику между приложениями без проверки фактических сервисов и данных.

## GitHub Pages и App Store Connect

Публикация готового HTML: Settings → Pages → Deploy from a branch → `main` → `/ (root)`. `.nojekyll` сохраняется в корне. Workflow `validate.yml` проверяет исходники и HTML, но не меняет настройки Pages и не выполняет отдельный деплой.
Файлы подготовлены для публикации из корня существующего репозитория; текущие настройки удалённого Pages проверяются отдельно.

Для каждой локали в App Store Connect используйте адреса из таблицы ниже. Из приложения открывайте документы непосредственно на языке интерфейса с запасным `en`. В этом изменении Swift-код приложения и настройки App Store Connect не изменяются.

| Язык | Marketing URL | Privacy Policy URL | Support URL | Terms URL |
| --- | --- | --- | --- | --- |
| en | https://napp-dev.github.io/apps/nyrecipes/en/ | https://napp-dev.github.io/apps/nyrecipes/en/privacy/ | https://napp-dev.github.io/apps/nyrecipes/en/support/ | https://napp-dev.github.io/apps/nyrecipes/en/terms/ |
| ru | https://napp-dev.github.io/apps/nyrecipes/ru/ | https://napp-dev.github.io/apps/nyrecipes/ru/privacy/ | https://napp-dev.github.io/apps/nyrecipes/ru/support/ | https://napp-dev.github.io/apps/nyrecipes/ru/terms/ |
| de | https://napp-dev.github.io/apps/nyrecipes/de/ | https://napp-dev.github.io/apps/nyrecipes/de/privacy/ | https://napp-dev.github.io/apps/nyrecipes/de/support/ | https://napp-dev.github.io/apps/nyrecipes/de/terms/ |
| pl | https://napp-dev.github.io/apps/nyrecipes/pl/ | https://napp-dev.github.io/apps/nyrecipes/pl/privacy/ | https://napp-dev.github.io/apps/nyrecipes/pl/support/ | https://napp-dev.github.io/apps/nyrecipes/pl/terms/ |

`app-ads.txt` сохранён без изменения существующей строки Google. Строки Яндекса добавляются из кабинета РСЯ, когда доступны подтверждённые seller ID; значения нельзя придумывать. Этот файл общий для приложений на домене.
Почта поддержки взята из существующих сайтов разработчика: `napp.dev.support@gmail.com`.
В публичный репозиторий не добавлять токены, конфигурацию Firebase приложения, персональные обращения пользователей и внутренние задачи.

## Weekwall

App Store: https://apps.apple.com/app/id6819834661. Только iPhone, iOS 26 и новее.
Исходники: `apps/weekwall/app.json` и `content/weekwall/<язык>/{privacy,terms,support}.md`.
В `assets/weekwall/` находятся иконка приложения и демонстрационный скриншот календаря на экране блокировки. Скриншот общий для всех языков; показанные события — демонстрационные.
Политика описывает текущую версию без рекламы, аналитики и сторонних crash SDK; при добавлении сервисов сначала пересмотреть тексты и все переводы.

| Локаль сайта | Локали App Store | Страница приложения |
| --- | --- | --- |
| en | en-US, en-GB, en-AU, en-CA | https://napp-dev.github.io/apps/weekwall/en/ |
| ru | ru | https://napp-dev.github.io/apps/weekwall/ru/ |
| de | de-DE | https://napp-dev.github.io/apps/weekwall/de/ |
| fr | fr-FR, fr-CA | https://napp-dev.github.io/apps/weekwall/fr/ |
| es | es-ES | https://napp-dev.github.io/apps/weekwall/es/ |
| es-419 | es-MX | https://napp-dev.github.io/apps/weekwall/es-419/ |
| pt-BR | pt-BR, pt-PT | https://napp-dev.github.io/apps/weekwall/pt-BR/ |
| it | it | https://napp-dev.github.io/apps/weekwall/it/ |
| ja | ja | https://napp-dev.github.io/apps/weekwall/ja/ |
| ko | ko | https://napp-dev.github.io/apps/weekwall/ko/ |

Marketing URL — страница приложения из таблицы. Privacy Policy URL, Terms URL и Support URL получаются добавлением `privacy/`, `terms/` и `support/` соответственно. Например: `https://napp-dev.github.io/apps/weekwall/es-419/privacy/`.
В приложении `WeekwallLinks` выбирает локаль по языку приложения; для неподдерживаемых языков используется `en`.
Переключение языка в документе сохраняет его тип. Числовой регион `es-419` поддерживается генератором.

Перед публикацией: собрать сайт, выполнить `--check`, посмотреть каталог и документы на широком и узком экране. После публикации проверить все 30 прямых адресов Weekwall и ссылки из приложения. Публикация идёт через существующий GitHub Pages из `main` / root; локальная сборка сама ничего не публикует.
