# Land & Crop Suitability Checker -- Team 17, Challenge 1

Pick a location, pick a crop, get an explainable suitability verdict
plus the climate/soil data behind it -- and optionally upload a leaf
photo to check for disease and get a treatment recommendation.

Built for Reboot the Earth 2026, Challenge 1. $0 budget: every data
source and model below is free and needs no paid API key.

## How it works

1. Click the map or type coordinates to choose a location.
2. Pick a crop from the dropdown; optionally upload a leaf photo.
3. Hit **Check this location**. The app:
   - pulls long-term temperature/rainfall/humidity for that point from
     **NASA POWER**,
   - pulls soil pH from **SoilGrids** (ISRIC),
   - scores the point against the crop's known comfortable ranges
     (`suitability.py`) and explains which factors passed/failed,
   - if a photo was uploaded, runs it through a pretrained leaf-disease
     classifier and looks up a treatment note for whatever it predicts.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

First run will download the disease-detection model (a few hundred MB) --
that's normal, it's cached after that.

## Deploy for free (for the live demo link / submission)

1. Push this folder to a **public** GitHub repo (required anyway --
   see Rules below).
2. Go to https://share.streamlit.io -> "New app" -> pick the repo,
   branch `main`, main file `app.py` -> Deploy.
3. First build takes a few minutes (installing torch). You get a
   public `*.streamlit.app` URL -- put that in your Unite Ideas
   submission and pitch.

## Before you build on top of this (do this first, ~15-20 min)

- `data_sources.py` was written against NASA POWER's and SoilGrids'
  documented response shapes, but couldn't be live-tested from the
  sandbox this was built in. Run `python data_sources.py <lat> <lon>`
  with real internet and read the printed JSON -- if a field comes
  back `None`, the fix is almost always a one-line key rename, marked
  with `# ADJUST` comments in that file. Better to catch this Thursday
  morning than mid-pitch.
- `crop_data.py`'s temperature/rainfall/pH ranges are ballpark
  agronomic estimates, not pulled live from FAO EcoCrop. Tighten any
  you have time for at https://ecocrop.review.fao.org.
- Try a few real leaf photos through the disease check and see what
  labels actually come back -- add any missing ones to
  `DISEASE_TREATMENTS` in `crop_data.py` (the exact label strings are
  printed in the app's "Other possibilities" expander).

## Left out on purpose (2-day, $0 scope)

- **AI chat bot** ("if possible" in the original plan) -- lowest
  priority. If time remains Friday: Google AI Studio's Gemini API
  free tier or Groq's free tier both work with no credit card, and
  it's a small addition -- a text box that sends the current
  verdict + climate/soil numbers as context to the model and streams
  back an answer.
- Weighted/AHP scoring or an ML-refined suitability score (see the
  team's original broader plan) -- the current equal-weighted rule in
  `suitability.py` is transparent and easy to defend to judges, which
  matters more than sophistication in the time available.
- More crops -- add entries to `CROP_THRESHOLDS` in `crop_data.py`,
  same shape as the existing ones.

## Data, model & library credits (required by the hackathon's
## "Original work and IP" rule)

- Climate data: **NASA POWER** (power.larc.nasa.gov), public domain.
- Soil data: **SoilGrids**, ISRIC -- World Soil Information
  (soilgrids.org), CC-BY 4.0.
- Map tiles: **OpenStreetMap** contributors, via Leaflet/Folium, ODbL.
- Disease model: `linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification`
  on Hugging Face, MobileNetV2 fine-tuned on the **PlantVillage**
  dataset.
- Libraries: Streamlit, Folium, streamlit-folium, Hugging Face
  Transformers, PyTorch, Pillow, Requests -- each under its own
  open-source license (see each project's repo).

## License

Pick one and add a LICENSE file -- MIT is the simplest fit for "open
source, open everything": https://choosealicense.com/licenses/mit/
