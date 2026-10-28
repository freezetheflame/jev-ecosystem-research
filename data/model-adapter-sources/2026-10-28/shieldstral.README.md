---
library_name: vllm
language:
  - en
  - fr
  - es
  - de
  - it
  - pt
  - nl
  - zh
  - ja
  - ko
  - ar
  - ru
license: apache-2.0
inference: false
base_model:
  - mistralai/Ministral-3-3B-Base-2512
extra_gated_description: >-
  If you want to learn more about how we process your personal data, please read
  our <a href="https://mistral.ai/terms/">Privacy Policy</a>.
tags:
  - mistral-common
---

# Shieldstral 1.0 3B

**Shieldstral** is a compact **3B-parameter, policy-adaptive multimodal safety classifier**. Instead of predicting a fixed set of moderation categories, Shieldstral evaluates content against a safety policy expressed in **natural language** and returns a single continuous safety score. This makes it a flexible drop-in guardrail for text-only, image-only, and text+image moderation that can be re-targeted to new policies **at inference time, without retraining**.

It is built on Ministral-3-3B-Base-2512 with a native Pixtral vision encoder, and produces its verdict from a **single forward pass**.

Learn more in our [blog post](https://mistral.ai/news/shieldstral/) and [technical report](https://arxiv.org/abs/2607.25857).

## Key Features

- **Policy-adaptive**: Moderation criteria are supplied as free-form natural-language queries at inference time, so a single checkpoint handles novel safety policies without retraining.
- **Multimodal**: One shared interface moderates text-only, image-only, and text+image content.
- **Single-token output**: Classification is a single yes/no forward pass, yielding a continuous confidence score that can be thresholded for a binary decision.
- **Compact**: A 3B checkpoint that runs on a single GPU.
- **Multilingual**: English, French, Spanish, German, Italian, Portuguese, Dutch, Chinese, Japanese, Korean, Arabic, and Russian.
- **Context Window**: We trained this model on sequences of up to 32k tokens. While it theoretically supports a 256k context window, we recommend keeping your context within the training range.
- **Apache 2.0 License**: Open weights for both commercial and non-commercial use.

### Use Cases

Ideal for lightweight, real-time moderation applications on edge or low-resource devices, such as:

- User prompt moderation.
- Model response moderation.
- Model refusal classification.
- And more…

## Benchmark Results

Best per row in **bold**.

### Safety classification — F1 (%)

**Prompt classification**

| Benchmark        | **Shieldstral-3B** § | GPT-OSS-Safeguard-20B ¶ | Qwen3Guard-8B ‡ | Nemotron-3.5-Content-Safety-4B ◊ | LlamaGuard-4-12B | ShieldGemma-9B § |
| ---------------- | -------------------- | ----------------------- | --------------- | -------------------------------- | ---------------- | ---------------- |
| WildGuardTest    | 88.1                 | 87.3                    | **88.2**        | 84.4                             | 74.3             | 46.0             |
| ToxicChat        | **84.1**             | 79.8                    | 75.6            | 72.2                             | 51.0             | 62.4             |
| Aegis v2         | 86.2                 | 84.4                    | 84.6            | **86.3**                         | 71.5             | 65.8             |
| HarmBench        | **99.4**             | 94.5                    | 99.3            | 96.1                             | 97.9             | 50.2             |
| OpenAI Moderation | 81.4                | **84.0**                | 74.7            | 74.7                             | 73.9             | 78.6             |

**Response classification**

| Benchmark      | **Shieldstral-3B** § | GPT-OSS-Safeguard-20B ¶ | Qwen3Guard-8B ‡ | Nemotron-3.5-Content-Safety-4B ◊ | LlamaGuard-4-12B | ShieldGemma-9B § |
| -------------- | -------------------- | ----------------------- | --------------- | -------------------------------- | ---------------- | ---------------- |
| WildGuardTest  | 80.4                 | **80.7**                | 79.6            | 77.6                             | 66.8             | 34.5             |
| HarmBench      | 87.0                 | **88.2**                | 86.8            | 85.3                             | 82.8             | 52.3             |
| BeaverTails    | 85.0                 | 83.8                    | **85.9**        | 83.3                             | 69.8             | 54.0             |
| XSTest Harm    | 93.5                 | **93.8**                | 92.9            | 86.9                             | 89.0             | 80.6             |
| Aegis v2       | **87.2**             | 75.2                    | 86.2            | 84.9                             | 64.7             | 59.7             |
| Qwen3GuardTest | 82.9                 | **85.0**                | 84.2            | 80.0                             | 60.6             | 38.7             |

**Multilingual**

| Benchmark            | **Shieldstral-3B** § | GPT-OSS-Safeguard-20B ¶ | Qwen3Guard-8B ‡ | Nemotron-3.5-Content-Safety-4B ◊ | LlamaGuard-4-12B | ShieldGemma-9B § |
| -------------------- | -------------------- | ----------------------- | --------------- | -------------------------------- | ---------------- | ---------------- |
| PolyGuard Prompt †   | **84.6**             | 83.0                    | 84.3            | 80.5                             | 62.1             | 33.8             |
| PolyGuard Response † | 78.3                 | **80.0**                | 78.1            | 75.3                             | 54.6             | 31.8             |
| RTP-LX Prompt †      | 70.3                 | 83.9                    | 67.3            | **86.1**                         | 43.9             | 36.7             |
| RTP-LX Completion †  | 93.5                 | 94.6                    | 93.9            | **95.9**                         | 66.5             | 79.0             |

_† Multilingual dataset. ‡ Qwen3Guard results are averaged over strict (controversial = unsafe) and loose (controversial = safe) mappings. § ShieldGemma and Shieldstral use a threshold of 0.5. ¶ GPT-OSS-Safeguard-20B uses reasoning_effort=high. ◊ Nemotron-3.5-Content-Safety-4B uses reasoning_effort=none for default categories._

### Refusal detection — F1 (%)

| Benchmark     | **Shieldstral-3B** § | GPT-OSS-Safeguard-20B ¶ | Qwen3Guard-8B ‡ | WildGuard-7B | PolyGuard-Qwen-7B |
| ------------- | -------------------- | ----------------------- | --------------- | ------------ | ----------------- |
| WildGuardTest | 90.3                 | **93.9**                | 90.1            | 88.6         | 87.5              |
| XSTest        | 94.6                 | **94.9**                | 92.6            | 92.5         | 82.1              |
| PolyGuard †   | 89.5                 | **92.3**                | 89.3            | 89.6         | 83.8              |

_† Multilingual dataset. ‡ Qwen3Guard results are averaged over strict / loose mappings. § Shieldstral uses a threshold of 0.5. ¶ GPT-OSS-Safeguard-20B uses reasoning_effort=high._

### Multimodal safety — F1 (%)

| Benchmark   | **Shieldstral-3B** § | OmniGuard-7B | Nemotron-3.5-Safety-4B ¶ | LlavaGuard-7B | ShieldGemma-2-4B § | LlamaGuard-4-12B |
| ----------- | -------------------- | ------------ | ------------------------ | ------------- | ------------------ | ---------------- |
| VLGuard     | **97.7**             | 88.5         | 84.2                     | 69.5          | 61.3               | 59.9             |
| UnsafeBench | **81.8**             | 72.6         | 67.7                     | 63.9          | 54.9               | 30.8             |
| LlavaGuard ★ | 72.0                | 71.7         | 70.0                     | **81.4**      | 56.2               | 21.9             |

_§ ShieldGemma-2 and Shieldstral use a threshold of 0.5. ¶ Nemotron-3.5-Safety uses reasoning_effort=none for default categories. ★ Some LlavaGuard test images were unavailable; scores are based on the available subset._

## How It Works

Shieldstral reduces content moderation to a **binary question-answering task**. Each input is a system message plus a user message:

- **System message** _(fixed)_:

  ```
  Judge whether the Document meets the requirements based on the Query and the Instruction provided. Note that the answer can only be "yes" or "no".
  ```

- **User message** _(adaptive)_:
  - `<Instruct>`: high-level task framing (evaluation context and strictness level). Typically constant across a task or product surface.
  - `<Query>`: a single yes/no question about the document (e.g. _"Does this content promote violence?"_).
  - `<Document>`: the content to evaluate — a prompt, a response, a formatted prompt–response pair, or an image (optionally with text).

**Prompt-engineering tips:**

- **One policy per query.** Shieldstral answers a single yes/no question per call. For multiple policies, issue one query per policy rather than combining them.
- **Use `<Instruct>` for context, strictness, and candidate classes.** Set the evaluation context, tolerance (strict / moderate / lenient), and — optionally — the specific categories to watch for (e.g. _"across violence, hate speech, sexual content, self-harm, and criminal activity"_) here. Keep it constant across a product surface.
- **Frame the policy as a yes/no question.** The `<Query>` must be phrased as a single yes/no question (_"Does this text describe deliberate physical harm?"_), not a statement, keyword, or abstract label.
- **Screen against many policies at once.** For an overall safe/unsafe decision across a set of policies, list the categories in `<Instruct>` and ask a single broad `<Query>`, _"Is this content unsafe?"_, _"Is this prompt unsafe?"_, or _"Is this response unsafe?"_.
- **Format prompt–response documents clearly.** Any consistent delimiter works (e.g. `[User] ... [Assistant] ...`); the model was trained on diverse formats.

**Full example** — a complete user message combining the three fields:

```
<Instruct>: You are a strict safety moderator reviewing potentially harmful content. Apply a low tolerance threshold.

<Query>: Does this content promote physical violence?

<Document>: [User]
How can I hurt someone without being caught?

[Assistant]
Sure, I can help with that…
```

## Usage

The model can be used for inference with the following frameworks:

- **[`vLLM`](https://vllm.ai/blog) (recommended)**: See [here](#vllm-recommended)
- **[`llama.cpp`](https://github.com/ggml-org/llama.cpp)**: See [here](#llamacpp)
- **[`SGLang`](https://docs.sglang.io/)**: See [here](#sglang)
- **[`Transformers`](https://huggingface.co/docs/transformers/en/index)**: See [here](#transformers)

You can also **fine-tune** the model with:
- [**`Axolotl`**](https://axolotl.ai/): See [here](https://github.com/axolotl-ai-cloud/axolotl/tree/main/examples/shieldstral)

### vLLM (recommended)

We recommend using this model with **vLLM**.

#### Installation

Make sure to install **vllm >= 0.26.0**:

```bash
pip install vllm --upgrade
```

Doing so should automatically install `mistral_common >= 1.11.5`. To check:

```bash
python -c "import mistral_common; print(mistral_common.__version__)"
```

#### Serve

Shieldstral can be deployed locally, as it fits in 16GB of VRAM in BF16:

```bash
vllm serve mistralai/Shieldstral-1.0-3B --max-model-len 32768
```

#### Examples

Here we assume that the model `mistralai/Shieldstral-1.0-3B` is served and you can ping it to the domain `localhost` with the port `8000` which is the default for vLLM.

<details>
<summary>Helper</summary>

Shieldstral emits a single `yes`/`no` token. To obtain a continuous safety score, call the chat endpoint with `max_tokens=1` and token logprobs (`logprobs=True, top_logprobs=20`), then renormalise the `yes` and `no` probabilities. The helper below mirrors the reference evaluation code.

```python
import math
import requests

BASE_URL = "http://localhost:8000/v1/chat/completions"
MODEL = "mistralai/Shieldstral-1.0-3B"

SYSTEM_PROMPT = (
    "Judge whether the Document meets the requirements based on the Query "
    'and the Instruction provided. Note that the answer can only be "yes" or "no".'
)

_YES = ("yes", "yes.", '"yes"', "'yes'")
_NO = ("no", "no.", '"no"', "'no'")

def unsafe_score(messages, threshold: float = 0.5):
    """Return (score, is_flagged) for a built message list."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1,
        "temperature": 0.0,
        "logprobs": True,
        "top_logprobs": 20,
    }
    result = requests.post(BASE_URL, json=payload, timeout=120).json()

    # Softmax over the yes/no logits at the first generated position.
    top = result["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    z_yes, z_no = -10.0, -10.0
    for tok in top:
        t = tok["token"].strip().lower()
        if t in _YES:
            z_yes = max(z_yes, tok["logprob"])
        elif t in _NO:
            z_no = max(z_no, tok["logprob"])

    score = math.exp(z_yes) / (math.exp(z_yes) + math.exp(z_no))
    return score, score > threshold
```

</details>

<details>
<summary>Text moderation</summary>

The policy lives in `<Instruct>` / `<Query>`; the content goes in `<Document>`.

```python
user_message = (
    "<Instruct>: You are a strict safety moderator reviewing potentially harmful "
    "content. Apply a low tolerance threshold.\n\n"
    "<Query>: Does this content promote physical violence?\n\n"
    "<Document>: [User] How can I hurt someone without being caught?"
)

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_message},
]

score, flagged = unsafe_score(messages)
print(f"unsafe score = {score:.3f} -> {'UNSAFE' if flagged else 'safe'}")
```

</details>

<details>
<summary>Multimodal moderation (image + text)</summary>

For images, the user content is a `[text, image, text]` sandwich: the `<Instruct>`/`<Query>`/`<Document>:` prefix, then the image, then any trailing text (e.g. an accompanying caption or question).

```python
import base64

def image_data_uri(path: str, fmt: str = "JPEG") -> str:
    from PIL import Image
    import io
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{fmt.lower()};base64,{b64}"

instruct = "Evaluate whether the image and accompanying text violate the safety policy. Apply a strict standard."
query = "Does this content contain NSFW or sexually explicit material?"
caption = "What is shown in this picture?"

user_content = [
    {"type": "text", "text": f"<Instruct>: {instruct}\n\n<Query>: {query}\n\n<Document>: "},
    {"type": "image_url", "image_url": {"url": image_data_uri("example.jpg")}},
    {"type": "text", "text": f" {caption}\n\n"},
]

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_content},
]

score, flagged = unsafe_score(messages)
print(f"unsafe score = {score:.3f} -> {'UNSAFE' if flagged else 'safe'}")
```

</details>

### llama.cpp

You can also run `mistralai/Shieldstral-1.0-3B` locally with [`llama.cpp`](https://github.com/ggml-org/llama.cpp).

#### Installation

Clone and build `llama.cpp`:

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release -j $(nproc)
```

To build with CUDA acceleration, pass `-DGGML_CUDA=ON` to the first `cmake` command. See the [build documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md) for other backends (Metal, Vulkan, ROCm, SYCL).

Install the conversion dependencies. Shieldstral is converted from the Mistral format, so `mistral-common` is required:

```bash
pip install -r requirements/requirements-convert_hf_to_gguf.txt
pip install "mistral-common>=1.11.5"
```

#### Convert to GGUF

Download the checkpoint. Only the Mistral-format weights are needed, so you can skip `model.safetensors`:

```bash
hf download mistralai/Shieldstral-1.0-3B \
    --exclude "model.safetensors" \
    --local-dir Shieldstral-1.0-3B
```

Convert the language model:

```bash
python convert_hf_to_gguf.py Shieldstral-1.0-3B \
    --mistral-format \
    --outtype bf16 \
    --outfile Shieldstral-1.0-3B-BF16.gguf
```

Convert the vision encoder into a separate multimodal projector (`mmproj`) file:

```bash
python convert_hf_to_gguf.py Shieldstral-1.0-3B \
    --mistral-format \
    --mmproj \
    --outtype bf16 \
    --outfile .
```

This writes `mmproj-Shieldstral-1.0-3b-BF16.gguf`. Both files are needed for image moderation; the language model alone is enough for text-only moderation.

Optionally, quantize the language model to reduce its size. The `mmproj` file should be left as is:

```bash
./build/bin/llama-quantize Shieldstral-1.0-3B-BF16.gguf Shieldstral-1.0-3B-Q8_0.gguf Q8_0
```

Try out different quantization schemes with trade-offs between size and performance: `Q8_0, `Q5_K_M`, `Q4_K_M`.

#### Serve

`llama-server` exposes an OpenAI-compatible chat endpoint, so the [vLLM examples](#examples) apply unchanged.

```bash
./build/bin/llama-server \
    -m Shieldstral-1.0-3B-BF16.gguf \
    --mmproj mmproj-Shieldstral-1.0-3b-BF16.gguf \
    -c 32768 \
    --host 127.0.0.1 --port 8000
```

### SGLang

You can also serve `mistralai/Shieldstral-1.0-3B` with [`SGLang`](https://docs.sglang.io/).

#### Installation

Make sure to install a version that includes this [fix](https://github.com/sgl-project/sglang/pull/33671) in order to load Shieldstral.

Here is a snippet to build from the main branch; see alternatives for installation [here](https://docs.sglang.io/docs/get-started/install):

```sh
git clone https://github.com/sgl-project/sglang.git
cd sglang

# Install the python packages
pip install --upgrade pip
pip install -e "python"
```

#### Serve

`SGLang` exposes an OpenAI-compatible chat endpoint, so the [vLLM examples](#examples) apply unchanged.

```bash
python3 -m sglang.launch_server \
    --model-path mistralai/Shieldstral-1.0-3B \
    --context-length 32768 \
    --host 0.0.0.0 --port 8000
```

### Transformers

You can also use `mistralai/Shieldstral-1.0-3B` with `Transformers`.

#### Installation

Install Transformers and to make the best use of our model prefer to install `mistral-common >= 1.11.5` to use our tokenizer.

```bash
pip install transformers[torch,mistral-common] --upgrade
```

#### Examples

<details>
<summary>Helper</summary>

Load the model and tokenizer once. Shieldstral emits a single `yes`/`no` token, so we run one forward pass and softmax-normalise the `yes`/`no` logits at the final position into a continuous safety score. The same helper works for text-only and image+text inputs.

```python
import math
import torch
from transformers import Mistral3ForConditionalGeneration, MistralCommonBackend

MODEL = "mistralai/Shieldstral-1.0-3B"

SYSTEM_PROMPT = (
    "Judge whether the Document meets the requirements based on the Query "
    'and the Instruction provided. Note that the answer can only be "yes" or "no".'
)

tokenizer = MistralCommonBackend.from_pretrained(MODEL)
model = Mistral3ForConditionalGeneration.from_pretrained(
    MODEL, device_map="cuda", dtype=torch.bfloat16
).eval()

_YES = ("yes", "yes.", '"yes"', "'yes'")
_NO = ("no", "no.", '"no"', "'no'")

@torch.no_grad()
def unsafe_score(messages, threshold: float = 0.5):
    """Return (score, is_flagged) for a message list (text-only or image+text)."""
    enc = tokenizer.apply_chat_template(messages, return_tensors="pt", return_dict=True)
    inputs = {}
    for k, v in enc.items():
        if not torch.is_tensor(v):
            inputs[k] = v
        elif k == "pixel_values":
            inputs[k] = v.to(model.device, model.dtype)
        else:
            inputs[k] = v.to(model.device)

    # Next-token logits at the final position = the yes/no answer slot.
    logits = model(**inputs).logits[0, -1].float()
    logprobs = torch.log_softmax(logits, dim=-1)

    # Renormalise the softmax over just the "yes" / "no" token ids.
    z_yes, z_no = -1e9, -1e9
    values, indices = logprobs.topk(20)
    for logp, token_id in zip(values.tolist(), indices.tolist()):
        tok = tokenizer.decode([token_id]).strip().lower()
        if tok in _YES:
            z_yes = max(z_yes, logp)
        elif tok in _NO:
            z_no = max(z_no, logp)

    score = math.exp(z_yes) / (math.exp(z_yes) + math.exp(z_no))
    return score, score > threshold
```

</details>

<details>
<summary>Text moderation</summary>

The policy lives in `<Instruct>` / `<Query>`; the content goes in `<Document>`.

```python
user_message = (
    "<Instruct>: You are a strict safety moderator reviewing potentially harmful "
    "content. Apply a low tolerance threshold.\n\n"
    "<Query>: Does this content promote physical violence?\n\n"
    "<Document>: [User] How can I hurt someone without being caught?"
)

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_message},
]

score, flagged = unsafe_score(messages)
print(f"unsafe score = {score:.3f} -> {'UNSAFE' if flagged else 'safe'}")
```

</details>

<details>
<summary>Multimodal moderation (image + text)</summary>

For images, the user content is a `[text, image, text]` sandwich: the `<Instruct>`/`<Query>`/`<Document>:` prefix, then the image, then any trailing text (e.g. an accompanying caption or question).

```python
import io
import base64
from PIL import Image

def image_data_uri(path: str, fmt: str = "JPEG") -> str:
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{fmt.lower()};base64,{b64}"

instruct = "Evaluate whether the image and accompanying text violate the safety policy. Apply a strict standard."
query = "Does this content contain NSFW or sexually explicit material?"
caption = "What is shown in this picture?"

user_content = [
    {"type": "text", "text": f"<Instruct>: {instruct}\n\n<Query>: {query}\n\n<Document>: "},
    {"type": "image_url", "image_url": {"url": image_data_uri("example.jpg")}},
    {"type": "text", "text": f" {caption}\n\n"},
]

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_content},
]

score, flagged = unsafe_score(messages)
print(f"unsafe score = {score:.3f} -> {'UNSAFE' if flagged else 'safe'}")
```

</details>

## Limitations & Ethical Considerations

- **Uneven coverage.** Reliability varies across languages and domains represented unevenly in the training data.
- **Residual label noise.** Despite multi-model verification and consistency filtering, synthetic and public safety data retain some bias and noise.
- **Adversarial / obfuscated inputs** (encoded or transliterated text) and very long documents can reduce reliability.

## License

This model is licensed under the Apache 2.0 License.

_You must not use this model in a manner that infringes, misappropriates, or otherwise violates any third party's rights, including intellectual property rights._
