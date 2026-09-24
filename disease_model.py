from PIL import Image
from transformers import AutoModelForImageClassification, MobileNetV2ImageProcessor
import torch

MODEL_NAME = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"


def load_model():
    # The original model uses the legacy MobileNetV2FeatureExtractor.
    # MobileNetV2ImageProcessor is the current equivalent.
    processor = MobileNetV2ImageProcessor(
        size={"shortest_edge": 256},
        crop_size={"height": 224, "width": 224},
        do_resize=True,
        do_center_crop=True,
        do_rescale=True,
        rescale_factor=1 / 255,
        do_normalize=True,
        image_mean=[0.5, 0.5, 0.5],
        image_std=[0.5, 0.5, 0.5],
    )

    model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
    model.eval()

    return processor, model


def predict(image: Image.Image, processor, model, top_k: int = 3):
    inputs = processor(
        images=image.convert("RGB"),
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

    k = min(top_k, probs.shape[0])
    top_probs, top_idxs = torch.topk(probs, k=k)

    results = []

    for prob, idx in zip(top_probs.tolist(), top_idxs.tolist()):
        raw_label = model.config.id2label[idx]
        plant, disease = _parse_label(raw_label)

        results.append({
            "plant": plant,
            "disease": disease,
            "raw_label": raw_label,
            "confidence": prob,
        })

    return results


def _parse_label(raw_label: str):
    # Handles labels such as:
    # "Tomato with Late Blight"
    # "Healthy Tomato Plant"
    # "Potato with Early Blight"

    label = raw_label.strip()

    if label.lower().startswith("healthy"):
        plant = label.replace("Healthy ", "").replace(" Plant", "").strip()
        disease = "Healthy"
        return plant, disease

    if " with " in label:
        plant, disease = label.split(" with ", 1)
        return plant.strip(), disease.strip()

    return label, "Unknown"
