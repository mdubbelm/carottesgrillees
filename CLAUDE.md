# CLAUDE.md - Carottes Grillées

Literaire blog met gedichten en verhalen van Jacob.

## Project Info

| Item | Waarde |
|------|--------|
| **Naam** | Carottes Grillées |
| **Type** | Literaire blog (gedichten, verhalen) |
| **Auteur** | Jacob |
| **Status** | Migratie van WordPress naar statische site |
| **Doel** | Archief behouden, toekomst: mogelijk weer actief |
| **URL** | carottesgrillees.nl |

## Tech Stack

- **Generator**: Hugo
- **Hosting**: GitHub Pages (of Netlify)
- **Content**: Markdown
- **Bron**: WordPress database export (Local Sites)

## Design Uitgangspunt

Het design moet zo veel mogelijk lijken op de originele site (2010-2018).
Referentie screenshots staan in `/reference/`.

## Team

| Naam | Rol | Focus |
|------|-----|-------|
| **Thomas** | Typograaf | Poëzie layout, leestypografie |
| **Anneke** | Frontend Developer | Hugo setup, CSS, responsive |
| **Kehrana** | UI Designer | Visueel design volgens origineel |
| **Sarah** | Content Designer | Content migratie, structuur |

## WordPress Bron

```
Locatie: /Users/monique/Local Sites/carottesgrillees/
Database: app/sql/local.sql
Uploads: app/public/wp-content/uploads/
Content: ~263 gepubliceerde items
Afbeeldingen: 352 bestanden (2010-2018)
```

## Commands

```bash
# Development
hugo server -D              # Lokale preview met drafts
hugo                        # Build naar public/

# Deploy
git push origin main        # Triggert GitHub Actions
```

## Content Structuur (voorstel)

```
content/
├── gedichten/              # Poëzie
│   └── YYYY-MM-DD-titel.md
├── verhalen/               # Proza
│   └── YYYY-MM-DD-titel.md
└── _index.md               # Homepage
```

## Migratie Stappen

1. [ ] WordPress database uitlezen
2. [ ] Content extraheren naar Markdown
3. [ ] Afbeeldingen kopiëren
4. [ ] Hugo theme bouwen (origineel design)
5. [ ] Testen
6. [ ] Deploy naar GitHub Pages
7. [ ] DNS instellen

## Belangrijke Aandachtspunten

### Voor Jacob (niet-technisch)
- Markdown is simpel: platte tekst met wat opmaak
- Later eventueel CMS-laag (Decap CMS) voor makkelijk bewerken
- Techniek moet niet in de weg zitten

### Typografie
- Poëzie: witruimte en regelval zijn betekenisvol
- Gebruik `white-space: pre-wrap` voor gedichten
- Serif font voor literaire sfeer

### Authenticiteit
- Origineel design respecteren
- Jacob's visie is leidend
