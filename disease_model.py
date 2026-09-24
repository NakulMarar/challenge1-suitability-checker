"""
disease_model.py
-----------------
Wraps a pretrained, openly-licensed plant disease classifier so the
rest of the app doesn't need to know anything about torch/transformers.

Model: linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification
  https://huggingface.co/linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification
  - MobileNetV2, fine-tuned on the PlantVillage dataset
  - 38 classes: 26 diseases + 12 "healthy" classes across common crops
    (tomato, potato, apple, corn, grape, pepper, and more)
  - Reported ~99.5% accuracy ON THE PLANTVILLAGE TEST SET, which is
    lab-condition photos: single leaf, plain background, even light.
    Real phone photos taken outdoors will score noticeably lower --
    say so if a judge asks. That's an honest, expected limitation for
    a free pretrained model on a 2-day build, not a bug to hide.

Credit this model (and the PlantVillage dataset it's trained on) in
your README -- "Original work and IP" in the hackathon rules requires
attribution for open-source dependencies you use.
"""

from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch

MODEL_NAME = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"


def load_model():
    """
    Loads processor + model once. In app.py, wrap this call with
    @st.cache_resource so Streamlit only downloads/loads it a single
    time per server, not on every widget interaction/rerun.
    """
    processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
    model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
    model.eval()
    return processor, model


def predict(image: Image.Image, processor, model, top_k: int = 3):
    """
    image: a PIL image (e.g. Image.open(uploaded_file) from
           st.file_uploader).
    Returns up to top_k dicts, sorted by confidence descending:
      {"plant": str, "disease": str, "raw_label": str, "confidence": float}
    """
    inputs = processor(images=image.convert("RGB"), return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

    k = min(top_k, probs.shape[0])
    top_probs, top_idxs = torch.topk(probs, k=k)

    results = []
    for prob, idx in zip(top_probs.tolist(), top_idxs.tolist()):
        raw_label = model.config.id2label[idx]  # e.g. "Tomato___Late_blight"
        plant, disease = _parse_label(raw_label)
        results.append({
            "plant": plant,
            "disease": disease,
            "raw_label": raw_label,
            "confidence": prob,
        })
    return results


def _parse_label(raw_label: str):
    """'Tomato___Late_blight' -> ('Tomato', 'Late Blight')."""
    parts = raw_label.split("___")
    plant = parts[0].replace("_", " ").replace("(", "").replace(")", "").strip()
    if len(parts) > 1:
        disease_raw = parts[1].replace("_", " ").strip()
        disease = "Healthy" if disease_raw.lower() == "healthy" else disease_raw.title()
    else:
        disease = "Unknown"
    return plant, disease
