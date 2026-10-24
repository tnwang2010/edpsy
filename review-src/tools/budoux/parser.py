# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# 取自 google/budoux v0.10.0 的 budoux/parser.py（Apache License 2.0，全文見同資料夾 LICENSE）。
# 修改：只保留 Parser.parse，移除 HTML 處理與其他語言的載入函式；
# 加上 load_zh_hant()，讀取同資料夾的繁體中文模型 zh-hant.json。
"""BudouX parser：把中文句子切成語意片段，供標題換行使用。"""

import json
import os

MODEL = os.path.join(os.path.dirname(__file__), 'zh-hant.json')


class Parser:
  """BudouX's Parser.

  The main parser object with a variety of class methods to provide semantic
  chunks and markups from the given input string.

  Attributes:
    _model: A dict mapping a feature (str) and its score (int).
  """

  def __init__(self, model: dict[str, dict[str, int]]):
    """Initializes the parser.

    Args:
      model (Dict[str, Dict[str, int]]): A dict mapping a feature and its score.
    """
    self._model = model
    self._base_score = -sum(sum(g.values()) for g in self._model.values()) * 0.5

  @property
  def model(self) -> dict[str, dict[str, int]]:
    return self._model

  def parse(self, sentence: str) -> list[str]:
    """Parses the input sentence and returns a list of semantic chunks.

    Args:
      sentence (str): An input sentence.

    Returns:
      A list of semantic chunks (List[str]).
    """
    if sentence == '':
      return []
    chunks = [sentence[0]]
    uw1 = self._model.get('UW1', {})
    uw2 = self._model.get('UW2', {})
    uw3 = self._model.get('UW3', {})
    uw4 = self._model.get('UW4', {})
    uw5 = self._model.get('UW5', {})
    uw6 = self._model.get('UW6', {})
    bw1 = self._model.get('BW1', {})
    bw2 = self._model.get('BW2', {})
    bw3 = self._model.get('BW3', {})
    tw1 = self._model.get('TW1', {})
    tw2 = self._model.get('TW2', {})
    tw3 = self._model.get('TW3', {})
    tw4 = self._model.get('TW4', {})
    for i in range(1, len(sentence)):
      score = self._base_score
      if i > 2:
        score += uw1.get(sentence[i - 3], 0)
      if i > 1:
        score += uw2.get(sentence[i - 2], 0)
      score += uw3.get(sentence[i - 1], 0)
      score += uw4.get(sentence[i], 0)
      if i + 1 < len(sentence):
        score += uw5.get(sentence[i + 1], 0)
      if i + 2 < len(sentence):
        score += uw6.get(sentence[i + 2], 0)

      if i > 1:
        score += bw1.get(sentence[i - 2 : i], 0)
      score += bw2.get(sentence[i - 1 : i + 1], 0)
      if i + 1 < len(sentence):
        score += bw3.get(sentence[i : i + 2], 0)

      if i > 2:
        score += tw1.get(sentence[i - 3 : i], 0)
      if i > 1:
        score += tw2.get(sentence[i - 2 : i + 1], 0)
      if i + 1 < len(sentence):
        score += tw3.get(sentence[i - 1 : i + 2], 0)
      if i + 2 < len(sentence):
        score += tw4.get(sentence[i : i + 3], 0)

      if score > 0:
        chunks.append(sentence[i])
      else:
        chunks[-1] += sentence[i]
    return chunks


def load_zh_hant() -> Parser:
  """載入繁體中文模型。"""
  with open(MODEL, encoding='utf-8') as f:
    return Parser(json.load(f))
