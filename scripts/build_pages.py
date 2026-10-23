#!/usr/bin/env python3
# coding: utf-8
"""Build the GitHub Pages hub from JSON metadata and a small Markdown subset."""
import argparse
from datetime import date
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
KINDS = ('privacy', 'terms', 'support')
SITE = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
ORIGIN = SITE['origin'].rstrip('/')
EMAIL = SITE['contact_email']
PAGES = {}

def e(value):
    return escape(str(value), quote=True)

def url(app, lang=None, kind=None):
    return '/apps/' + app['id'] + '/' + (lang + '/' if lang else '') + (kind + '/' if kind else '')

def anchor(label, target, cls='', extra=''):
    return f'<a href="{e(target)}"' + (f' class="{e(cls)}"' if cls else '') + (f' {extra}' if extra else '') + f'>{e(label)}</a>'

def markdown(source):
    """Deliberately limited: headings, paragraphs, flat lists, links and bold."""
    def inline(value):
        result, cursor = [], 0
        for match in re.finditer(r'\[([^\]\n]+)\]\(([^\s)]+)\)', value):
            result.append(bold(value[cursor:match.start()]))
            target = match[2]
            scheme = urlsplit(target).scheme
            if scheme and scheme not in ('https', 'mailto'):
                raise ValueError(f'Unsafe link: {target}')
            result.append(anchor(match[1], target))
            cursor = match.end()
        result.append(bold(value[cursor:]))
        return ''.join(result)
    def bold(value):
        parts = value.split('**')
        if len(parts) % 2 == 0:
            raise ValueError('Unbalanced bold markup')
        return ''.join(f'<strong>{e(p)}</strong>' if i % 2 else e(p) for i, p in enumerate(parts))
    blocks, headings, paragraph, items = [], [], [], []
    title = None
    def flush():
        if paragraph:
            blocks.append('<p>' + inline(' '.join(paragraph)) + '</p>')
            paragraph.clear()
        if items:
            blocks.append('<ul>' + ''.join('<li>' + inline(x) + '</li>' for x in items) + '</ul>')
            items.clear()
    for line in source.splitlines():
        if not line.strip():
            flush()
        elif line.startswith('# '):
            flush()
            if title is not None:
                raise ValueError('Multiple document titles')
            title = line[2:]
        elif line.startswith('## '):
            flush()
            label = line[3:]
            heading_id = 'section-' + str(len(headings) + 1)
            headings.append((label, heading_id))
            blocks.append(f'<h2 id="{heading_id}">{e(label)}</h2>')
        elif line.startswith('- '):
            if paragraph:
                flush()
            items.append(line[2:])
        elif line.startswith(('#', '<', '```', '|', '---')):
            raise ValueError(f'Unsupported Markdown: {line}')
        else:
            if items:
                flush()
            paragraph.append(line.strip())
    flush()
    if not title or not headings:
        raise ValueError('Document requires a title and sections')
    return title, '\n'.join(blocks), headings

def languages(app, lang=None, kind=None):
    links = []
    for code, text in app['locales'].items():
        extra = f'hreflang="{e(code)}" lang="{e(code)}"'
        if code == lang:
            extra += ' aria-current="page"'
        links.append(anchor(text['label'], url(app, code, kind), 'language', extra))
    label = app['locales'][lang]['choose'] if lang else 'Choose your language / Выберите язык'
    return f'<nav class="languages" aria-label="{e(label)}">' + ''.join(links) + '</nav>'

def document_links(app, lang, current=None):
    text = app['locales'][lang]
    return '<nav class="document-nav" aria-label="' + e(text['documents']) + '">' + ''.join(
        anchor(text[k], url(app, lang, k), extra='aria-current="page"' if k == current else '') for k in KINDS) + '</nav>'

def page(path, title, description, body, lang='en', app=None, kind=None, indexable=True):
    text = app['locales'][lang] if app and lang in app['locales'] else None
    all_apps = text['all_apps'] if text else 'All apps'
    skip = text['skip'] if text else 'Skip to content'
    contact = text['contact'] if text else 'Contact support'
    alternates = ''
    if app and text:
        alternates = ''.join(f'<link rel="alternate" hreflang="{e(code)}" href="{e(ORIGIN + url(app, code, kind))}">' for code in app['locales'])
        alternates += f'<link rel="alternate" hreflang="x-default" href="{e(ORIGIN + url(app))}">'
    og_image = app['icon'] if app else apps[0]['icon']
    content = f'''<!doctype html>
<html lang="{e(lang)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · {e(SITE['brand'])}</title><meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(ORIGIN + path)}">{alternates}
<meta name="color-scheme" content="light dark"><meta name="theme-color" content="#20483d">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{e(ORIGIN + path)}"><meta property="og:image" content="{e(ORIGIN + og_image)}">
<link rel="icon" href="{e(app['icon'] if app else '/assets/favicon.svg')}"><link rel="stylesheet" href="/assets/style.css">{'' if indexable else '<meta name="robots" content="noindex">'}</head>
<body><a class="skip" href="#main">{e(skip)}</a><header class="site-header"><div class="shell header-inner">{anchor(SITE['brand'], '/', 'brand')}<span class="header-links">{anchor(all_apps, '/')}{anchor(contact, 'mailto:' + EMAIL)}</span></div></header>
<main id="main" class="shell">{body}</main><footer class="shell footer"><span>© {e(SITE['brand'])}</span>{anchor(EMAIL, 'mailto:' + EMAIL)}</footer></body></html>'''
    target = path.lstrip('/') + 'index.html' if path.endswith('/') else path.lstrip('/')
    PAGES[target] = content + '\n'

apps = []
for app_id in SITE['apps']:
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', app_id):
        raise ValueError('App IDs must be stable lowercase slugs')
    app = json.loads((ROOT / 'apps' / app_id / 'app.json').read_text(encoding='utf-8'))
    if app['id'] != app_id or 'en' not in app['locales']:
        raise ValueError('App ID mismatch or missing English fallback')
    date.fromisoformat(app['updated'])
    apps.append(app)
    cards = ''.join(f'<a class="locale-card" href="{e(url(app, code))}" lang="{e(code)}"><span>{e(text["label"])}</span><strong>{e(text["name"])}</strong><span aria-hidden="true">↗</span></a>' for code, text in app['locales'].items())
    page(url(app), app['locales']['en']['name'], app['locales']['en']['description'],
         f'<div class="breadcrumbs">{anchor("All apps", "/")}<span aria-hidden="true">/</span><span>{e(app["locales"]["en"]["name"])}</span></div><section class="selector-intro"><img class="app-icon" src="{e(app["icon"])}" alt="" width="104" height="104"><p class="eyebrow">{e(app["locales"]["en"]["name"])}</p><h1>{e(app["locales"]["en"]["name"])}</h1><p class="lead">Choose your language for the app overview, download, documents and support.</p><p class="muted" lang="ru">Выберите язык: описание приложения, скачивание, документы и поддержка.</p></section><div class="locale-grid">{cards}</div>', app=app)
    for lang, text in app['locales'].items():
        if not re.fullmatch(r'[a-z]{2}(?:-(?:[A-Z]{2}|[0-9]{3}))?', lang):
            raise ValueError('Invalid language code')
        crumbs = f'<div class="breadcrumbs">{anchor(text["all_apps"], "/")}<span aria-hidden="true">/</span>{anchor(text["name"], url(app))}</div>'
        top = crumbs + languages(app, lang)
        features = ''.join(f'<div class="feature"><span class="feature-number">0{i}</span><h2>{e(f[0])}</h2><p>{e(f[1])}</p></div>' for i, f in enumerate(text['features'], 1))
        links = ''.join(f'<a class="document-card" href="{e(url(app, lang, k))}"><span class="doc-number">0{i}</span><strong>{e(text[k])}</strong><span aria-hidden="true">↗</span></a>' for i, k in enumerate(KINDS, 1))
        page(url(app, lang), text['name'], text['description'], top + f'''<section class="app-hero"><div class="hero-copy"><img class="app-icon" src="{e(app['icon'])}" width="88" height="88" alt=""><p class="eyebrow">{e(text['name'])}</p><h1>{e(text['tagline'])}</h1><p class="lead">{e(text['description'])}</p>{anchor(text['download'] + ' ↗', app['store_url'], 'button')}<p class="small muted">{e(text['platform'])}</p></div><div class="hero-photo{" phone-preview" if app.get("image_style") == "phone" else ""}"><img src="{e(app['hero'])}" alt="" width="1536" height="1024" fetchpriority="high"></div></section><section class="features">{features}</section><section class="documents-section"><p class="eyebrow">{e(text['name'])}</p><h2>{e(text['documents'])}</h2><p class="muted">{e(text['documents_intro'])}</p><div class="document-grid">{links}</div><p class="privacy-note">{e(text['privacy_note'])}</p></section>''', lang, app)
        for kind in KINDS:
            source = ROOT / 'content' / app_id / lang / (kind + '.md')
            raw = source.read_text(encoding='utf-8').replace('{{app_name}}', text['name']).replace('{{contact_email}}', EMAIL)
            if '{{' in raw or '}}' in raw:
                raise ValueError(f'Unresolved template in {source}')
            title, article, headings = markdown(raw)
            if title != text[kind]:
                raise ValueError(f'Document title mismatch: {source}')
            toc = '<aside class="toc"><p class="eyebrow">' + e(text['on_page']) + '</p><nav aria-label="' + e(text['on_page']) + '">' + ''.join(anchor(label, '#' + hid) for label, hid in headings) + '</nav></aside>'
            description = text['name'] + ' — ' + title
            page(url(app, lang, kind), description, description,
                 crumbs + languages(app, lang, kind) + document_links(app, lang, kind) + f'<header class="document-title"><p class="eyebrow">{e(text["name"])}</p><h1>{e(title)}</h1><p class="muted">{e(text["updated"])}: <time datetime="{e(app["updated"])}">{e(app["updated"])}</time></p></header><div class="document-layout">{toc}<article class="prose">{article}<div class="back-link">{anchor("← " + text["back"], url(app, lang))}</div></article></div>', lang, app, kind)

cards = ''
for app in apps:
    text = app['locales']['en']
    cards += f'<article class="app-card"><div class="app-card-copy"><img class="app-icon" src="{e(app["icon"])}" alt="" width="80" height="80"><p class="eyebrow">{e(app.get("catalogue_platform", "IPHONE & IPAD"))} · {len(app["locales"])} LANGUAGES</p><h2>{anchor(text["name"], url(app))}</h2><p class="native-name" lang="ru">{e(app["locales"].get("ru",text)["name"])}</p><p>{e(text["description"])}</p>{anchor("Explore the app ↗", url(app), "text-link")}</div><a class="app-card-image{" phone-preview" if app.get("image_style") == "phone" else ""}" href="{e(url(app))}" aria-label="{e(text["name"])}"><img src="{e(app["hero"])}" alt="" width="1536" height="1024"></a></article>'
page('/', 'Our apps', 'Napp apps: discover our apps, download them and find privacy policies, terms and support.', '<section class="hub-intro"><p class="eyebrow">INDEPENDENT APPS BY NAPP</p><h1>A little help.<br>For everyday life.</h1><p class="lead">Discover our apps. Find your language, the details<br class="desktop-break"> and a way to get in touch.</p></section><section class="catalogue" aria-labelledby="apps-title"><div class="section-heading"><h2 id="apps-title">Our apps</h2><span class="muted">' + f'{len(apps):02d}' + '</span></div>' + cards + '</section><section class="contact-strip"><h2>Need a hand?</h2><p>Support and documents are on each app’s page.</p>' + anchor(EMAIL, 'mailto:' + EMAIL) + '</section>')
page('/404.html', 'Page not found', 'This page could not be found.', '<section class="hub-intro"><p class="eyebrow">404</p><h1>Let’s find your way back.</h1><p class="lead">This address does not lead to a page.</p>' + anchor('Browse our apps →', '/', 'button') + '</section>', indexable=False)

sitemap = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
for path in sorted(PAGES):
    if path == '404.html':
        continue
    item = ET.SubElement(sitemap, 'url')
    ET.SubElement(item, 'loc').text = ORIGIN + '/' + path.removesuffix('index.html')
PAGES['sitemap.xml'] = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(sitemap, encoding='unicode') + '\n'
PAGES['robots.txt'] = f'User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n'

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.ids, self.h1, self.lang = [], set(), 0, None
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'html':
            self.lang = values.get('lang')
        if tag == 'h1':
            self.h1 += 1
        if 'id' in values:
            if values['id'] in self.ids:
                raise ValueError('Duplicate HTML id')
            self.ids.add(values['id'])
        for key in ('href', 'src'):
            if key in values:
                self.refs.append(values[key])

inspectors = {}
for path, content in PAGES.items():
    if path.endswith('.html'):
        parser = Inspector()
        parser.feed(content)
        if parser.h1 != 1 or not parser.lang:
            raise ValueError(f'Expected one H1 and language: {path}')
        inspectors[path] = parser
for path, parser in inspectors.items():
    for ref in parser.refs:
        parsed = urlsplit(ref)
        if parsed.scheme and parsed.scheme not in ('https', 'mailto'):
            raise ValueError(f'Unsafe URL in {path}: {ref}')
        if parsed.netloc and parsed.netloc != urlsplit(ORIGIN).netloc or parsed.scheme == 'mailto':
            continue
        if parsed.path:
            resolved = (ROOT / unquote(parsed.path.lstrip('/'))) if parsed.path.startswith('/') else (ROOT / path).parent / unquote(parsed.path)
            resolved = resolved.resolve()
            if not resolved.is_relative_to(ROOT):
                raise ValueError(f'Link escapes root: {ref}')
            target = resolved.relative_to(ROOT).as_posix()
            if parsed.path.endswith('/'):
                target = target.rstrip('/') + '/index.html' if target != '.' else 'index.html'
        else:
            target = path
        if target not in PAGES and not (ROOT / target).is_file():
            raise ValueError(f'Broken local link in {path}: {ref} -> {target}')
        if parsed.fragment and target in inspectors and unquote(parsed.fragment) not in inspectors[target].ids:
            raise ValueError(f'Missing anchor in {path}: {ref}')

args = argparse.ArgumentParser()
args.add_argument('--check', action='store_true', help='Validate without changing files; fail on stale output')
opts = args.parse_args()
changed = []
for path, content in PAGES.items():
    target = ROOT / path
    if not target.exists() or target.read_text(encoding='utf-8') != content:
        changed.append(path)
        if not opts.check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
if opts.check and changed:
    raise SystemExit('Generated files are missing or stale:\n' + '\n'.join(changed) + '\nRun python3 scripts/build_pages.py')
print(f'Validated {len(inspectors)} HTML pages, all local links, anchors and languages; ' + ('output is current.' if opts.check else f'wrote {len(changed)} files.'))
