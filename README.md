# Poke_Scraper

## 1) Architecture mise en place
- Source: **Bulbapedia** (liste par Pokédex National)
- Compute: **EC2** (Amazon Linux 2023) exécutant `scraper.py`
- Stockage: **S3** (objets publics pour l'exercice) sous `images/Generation_<I..IX>/...`
- IAM: **rôle d'instance** (least privilege)

Voir `architecture.drawio` (éditable).

## 2) Choix techniques
- `requests` + `BeautifulSoup` → parsing HTML robuste
- URLs d'images extraites depuis les miniatures; conversion en **URL originale** (suppression du segment `/thumb/.../SIZEpx-`)
- Catégorisation par **génération**
- **Tenacity** pour retries; **logging** structuré; **.env** pour la config
- Respect de **robots.txt** (Bulbapedia: crawl-delay=5s)
- Upload S3 avec `ACL public-read` + `SSE-S3` (bonne pratique)

## 3) Démo EC2 → S3
1. Créez un **rôle IAM** pour EC2 avec permissions S3 minimales (voir `README.md` plus complet dans le zip si besoin).
2. Lancez une instance **Amazon Linux 2023** (t3.micro) et attachez le rôle.
3. Installez Python et deps, configurez `.env`, exécutez `python scraper.py`.
4. Ouvrez la **console S3** et vérifiez les objets sous `images/Generation_*/*`. Testez une URL publique.

## 4) Lancer localement
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # éditez S3_BUCKET etc.
python scraper.py
# ou dry-run (sans download/upload):
DRY_RUN=true python scraper.py
```
