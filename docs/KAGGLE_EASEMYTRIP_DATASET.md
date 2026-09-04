# Kaggle EaseMyTrip Dataset Note

**Dataset slug:** `shubhambathwal/flight-price-prediction`  
**Dataset page:** https://www.kaggle.com/datasets/shubhambathwal/flight-price-prediction  
**License:** CC0-1.0, reported by Kaggle CLI during download on 2026-09-04  
**Local target folder:** `D:\Programming\hackathon2026\sih26056\data\raw\kaggle\easemytrip-flight-price-prediction\`

The full dataset is intentionally not tracked in git. Raw data belongs under `data/raw/`, which is ignored by `.gitignore`.

## Download Command

Run:

```powershell
py -m kaggle datasets download -d shubhambathwal/flight-price-prediction -p data\raw\kaggle\easemytrip-flight-price-prediction --unzip
```

Downloaded files confirmed locally on 2026-09-04:

| File | Purpose |
|---|---|
| `Clean_Dataset.csv` | Combined economy/business panel; 300,153 records |
| `economy.csv` | Economy-only records |
| `business.csv` | Business-only records |

## APIx-Relevant Columns

The Kaggle page describes a panel of EaseMyTrip flight booking options for Indian metro routes. The key modeling fields for APIx are:

| Field concept | APIx use |
|---|---|
| airline / carrier | matched-sample elementary relatives |
| flight number | quote identity and deduplication |
| source city / destination city | route basket mapping |
| departure / arrival timing | route-service quality controls |
| stops | quality segmentation |
| class | fare-class segmentation |
| duration | plausibility and quality checks |
| `days_left` | advance-purchase window mapping |
| price | total fare input to index tests |

## License Check

The dataset remained indexed on Kaggle on 2026-09-04 and the Kaggle CLI reported `License(s): CC0-1.0` during download. Still credit the Kaggle dataset page in project documentation and avoid committing the raw CSVs.
