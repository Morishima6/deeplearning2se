"""使用 Qwen2.5-Coder + QLoRA 训练函数级漏洞分类器。"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import torch
import yaml
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

from io_utils import read_jsonl
from paths import HF_CACHE_DIR
from utils_seed import set_seed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-train-samples", "--max_train_samples", dest="max_train_samples", type=int, default=None)
    parser.add_argument("--max-eval-samples", "--max_eval_samples", dest="max_eval_samples", type=int, default=None)
    parser.add_argument("--cache-dir", default=HF_CACHE_DIR)
    parser.add_argument("--run-suffix", default="")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_rows(path: str, text_field: str, max_samples: int | None) -> list[dict[str, Any]]:
    rows = read_jsonl(Path(path))
    if max_samples is not None:
        rows = rows[:max_samples]
    return [{"text": str(row[text_field]), "label": int(row["label"]), "id": row.get("id")} for row in rows]


class JsonlTextDataset(torch.utils.data.Dataset):
    def __init__(self, rows: list[dict[str, Any]], tokenizer: Any, max_length: int) -> None:
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = self.rows[idx]
        encoded = self.tokenizer(
            row["text"],
            truncation=True,
            max_length=self.max_length,
        )
        encoded["labels"] = row["label"]
        return encoded


def sigmoid_scores(logits: np.ndarray) -> np.ndarray:
    if logits.shape[1] == 1:
        return 1.0 / (1.0 + np.exp(-logits[:, 0]))
    exp_logits = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
    return probs[:, 1]


def find_best_threshold(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float]:
    thresholds = np.linspace(0.05, 0.95, 181)
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in thresholds:
        y_pred = (y_score >= threshold).astype(int)
        current_f1 = f1_score(y_true, y_pred, zero_division=0)
        if current_f1 > best_f1:
            best_threshold = float(threshold)
            best_f1 = float(current_f1)
    return best_threshold, best_f1


def compute_metrics_at_threshold(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict[str, Any]:
    y_pred = (y_score >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = [int(value) for value in cm.ravel()]
    result = {
        "threshold": round(threshold, 4),
        "accuracy": round(accuracy_score(y_true, y_pred), 6),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 6),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 6),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 6),
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }
    if len(np.unique(y_true)) == 2:
        result["roc_auc"] = round(roc_auc_score(y_true, y_score), 6)
        result["pr_auc"] = round(average_precision_score(y_true, y_score), 6)
    else:
        result["roc_auc"] = None
        result["pr_auc"] = None
    return result


def trainer_metrics(eval_pred: Any) -> dict[str, float]:
    logits, labels = eval_pred
    scores = sigmoid_scores(np.asarray(logits))
    preds = (scores >= 0.5).astype(int)
    return {
        "accuracy": accuracy_score(labels, preds),
        "precision": precision_score(labels, preds, zero_division=0),
        "recall": recall_score(labels, preds, zero_division=0),
        "f1": f1_score(labels, preds, zero_division=0),
    }


def write_predictions(rows: list[dict[str, Any]], y_true: np.ndarray, y_score: np.ndarray, threshold: float, out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "label", "prob_vulnerable", "prediction"])
        writer.writeheader()
        for row, label, score in zip(rows, y_true, y_score):
            writer.writerow(
                {
                    "id": row.get("id"),
                    "label": int(label),
                    "prob_vulnerable": round(float(score), 8),
                    "prediction": int(score >= threshold),
                }
            )


def main() -> None:
    args = parse_args()
    cfg = load_config(Path(args.config))
    set_seed(args.seed)

    model_name = cfg["model_name"]
    text_field = cfg["text_field"]
    output_dir = Path(cfg["output_dir"].format(seed=args.seed) + args.run_suffix)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    train_rows = load_rows(cfg["train_file"], text_field, args.max_train_samples)
    valid_rows = load_rows(cfg["valid_file"], text_field, args.max_eval_samples)
    test_rows = load_rows(cfg["test_file"], text_field, args.max_eval_samples)

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        cache_dir=args.cache_dir,
        token=False,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    device_map = None
    if torch.cuda.is_available():
        local_rank = int(os.environ.get("LOCAL_RANK", "0"))
        device_map = {"": local_rank}
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        quantization_config=quant_config,
        device_map=device_map,
        trust_remote_code=True,
        cache_dir=args.cache_dir,
        token=False,
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    lora_cfg = cfg["lora"]
    model = get_peft_model(
        model,
        LoraConfig(
            task_type=TaskType.SEQ_CLS,
            r=int(lora_cfg["r"]),
            lora_alpha=int(lora_cfg["alpha"]),
            lora_dropout=float(lora_cfg["dropout"]),
            target_modules=list(lora_cfg["target_modules"]),
            bias="none",
        ),
    )

    max_length = int(cfg["max_length"])
    train_dataset = JsonlTextDataset(train_rows, tokenizer, max_length)
    valid_dataset = JsonlTextDataset(valid_rows, tokenizer, max_length)
    test_dataset = JsonlTextDataset(test_rows, tokenizer, max_length)

    train_cfg = cfg["training"]
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=float(train_cfg["epochs"]),
        per_device_train_batch_size=int(train_cfg["per_device_train_batch_size"]),
        per_device_eval_batch_size=int(train_cfg["per_device_eval_batch_size"]),
        gradient_accumulation_steps=int(train_cfg["gradient_accumulation_steps"]),
        learning_rate=float(train_cfg["learning_rate"]),
        weight_decay=float(train_cfg["weight_decay"]),
        warmup_ratio=float(train_cfg["warmup_ratio"]),
        logging_steps=int(train_cfg["logging_steps"]),
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        metric_for_best_model="f1",
        greater_is_better=True,
        load_best_model_at_end=True,
        fp16=bool(train_cfg.get("fp16", True)),
        seed=args.seed,
        report_to=[],
        ddp_find_unused_parameters=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=trainer_metrics,
    )

    trainer.train()
    trainer.save_model(str(output_dir / "best_adapter"))

    valid_pred = trainer.predict(valid_dataset)
    test_pred = trainer.predict(test_dataset)
    valid_scores = sigmoid_scores(valid_pred.predictions)
    test_scores = sigmoid_scores(test_pred.predictions)
    y_valid = np.asarray([row["label"] for row in valid_rows], dtype=np.int64)
    y_test = np.asarray([row["label"] for row in test_rows], dtype=np.int64)

    threshold, valid_best_f1 = find_best_threshold(y_valid, valid_scores)
    metrics = {
        "model": model_name,
        "text_field": text_field,
        "seed": args.seed,
        "valid_best_f1": round(valid_best_f1, 6),
        "valid": compute_metrics_at_threshold(y_valid, valid_scores, threshold),
        "test": compute_metrics_at_threshold(y_test, test_scores, threshold),
    }

    (output_dir / "eval.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    write_predictions(valid_rows, y_valid, valid_scores, threshold, output_dir / "valid_predictions.csv")
    write_predictions(test_rows, y_test, test_scores, threshold, output_dir / "test_predictions.csv")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
