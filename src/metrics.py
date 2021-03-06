import numpy as np

from transformers.trainer_utils import PredictionOutput
from transformers import Wav2Vec2Processor, Wav2Vec2ProcessorWithLM
import datasets as hfd


def parse_w2v2_predictions_batched(pred: PredictionOutput, processor: Wav2Vec2Processor):
    """
    Parse trainer.predict() output obtained with Wav2Vec2 model
    using Processor for Acoustic Model only
    """
    pred_logits = pred.predictions
    pred_ids = np.argmax(pred_logits, axis=-1)
    pred_text = processor.batch_decode(pred_ids)

    # convert loss-ignore-token to pad token
    pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id
    # do not group tokens for ground truth texts
    text = processor.batch_decode(pred.label_ids, group_tokens=False)

    return {'pred_text': pred_text, 'text': text}


def parse_w2v2_predictions_batched_with_lm(pred: PredictionOutput, processor_with_lm: Wav2Vec2ProcessorWithLM):
    """
    Parse trainer.predict() output obtained with Wav2Vec2 model
    using Processor with Language model provided.
    """
    pred_logits = pred.predictions
    pred_text = processor_with_lm.batch_decode(pred_logits)['text']

    # convert loss-ignore-token to pad token
    pred.label_ids[pred.label_ids == -100] = processor_with_lm.tokenizer.pad_token_id
    # do not group tokens for ground truth texts
    text = processor_with_lm.tokenizer.batch_decode(pred.label_ids, group_tokens=False)

    return {'pred_text': pred_text, 'text': text}


class WerMetric:
    def __init__(self, processor: Wav2Vec2Processor):
        self.wer_metric = hfd.load_metric('wer')
        self.processor = processor

    def compute_metrics(self, pred: PredictionOutput):
        parsed_preds = parse_w2v2_predictions_batched(pred=pred, processor=self.processor)
        wer = self.wer_metric.compute(predictions=parsed_preds['pred_text'], references=parsed_preds['text'])
        return {"wer": wer}


class WerMetricWithLM:
    def __init__(self, processor_with_lm: Wav2Vec2ProcessorWithLM):
        self.wer_metric = hfd.load_metric('wer')
        self.processor_with_lm = processor_with_lm

    def compute_metrics(self, pred: PredictionOutput):
        parsed_preds = parse_w2v2_predictions_batched_with_lm(pred, processor_with_lm=self.processor_with_lm)
        wer = self.wer_metric.compute(predictions=parsed_preds['pred_text'], references=parsed_preds['text'])
        return {"wer": wer}
