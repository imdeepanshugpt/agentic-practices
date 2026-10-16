# Vector Embeddings for Documents: The Complete Guide

*How computers turn text into numbers that capture meaning, and how to build search and retrieval systems on top of that.*

---

## Table of Contents

1. [The Big Idea in Simple Words](#1-the-big-idea-in-simple-words)
2. [Why We Need Embeddings](#2-why-we-need-embeddings)
3. [A Short History: How Text Became Vectors](#3-a-short-history-how-text-became-vectors)
4. [How a Modern Embedding Model Works (Step by Step)](#4-how-a-modern-embedding-model-works-step-by-step)
5. [How Embedding Models Are Trained](#5-how-embedding-models-are-trained)
6. [Measuring Similarity](#6-measuring-similarity)
7. [The Document Embedding Pipeline](#7-the-document-embedding-pipeline)
8. [Chunking Strategies in Depth](#8-chunking-strategies-in-depth)
9. [Searching Vectors Fast: ANN Algorithms](#9-searching-vectors-fast-ann-algorithms)
10. [Vector Databases and Storage](#10-vector-databases-and-storage)
11. [Retrieval-Augmented Generation (RAG)](#11-retrieval-augmented-generation-rag)
12. [Hybrid Search and Reranking](#12-hybrid-search-and-reranking)
13. [Hands-On Code Examples](#13-hands-on-code-examples)
14. [Evaluating Retrieval Quality](#14-evaluating-retrieval-quality)
15. [Choosing a Model and Tuning Dimensions](#15-choosing-a-model-and-tuning-dimensions)
16. [Production Considerations](#16-production-considerations)
17. [Common Pitfalls and Best Practices](#17-common-pitfalls-and-best-practices)
18. [FAQ](#18-faq)
19. [Glossary](#19-glossary)
20. [Further Reading](#20-further-reading)

---

## 1. The Big Idea in Simple Words

Imagine a giant map. On this map, every document in the world has a pin. The rule of the map is:

> **Documents that mean similar things are placed close together. Documents that mean different things are placed far apart.**

A recipe for paneer butter masala sits near a recipe for dal makhani. Both are far from a document about quantum physics. A document about "car repair" sits near one about "fixing automobiles", even though they share no words.

An **embedding** is simply the **address of that pin on the map**. But instead of 2 coordinates (latitude, longitude), the map has hundreds or thousands of dimensions:

```
"How do I reset my password?"  →  [0.021, -0.113, 0.487, ..., 0.092]   (e.g. 768 numbers)
```

That list of numbers is called a **vector**. Once text is a vector, the computer can do math on meaning:

- **Closeness of two vectors** = similarity of two meanings.
- **Searching** = "find the pins closest to my question's pin."

That's the entire idea. Everything else in this document is about *how* the addresses are computed, *how* we store them, and *how* we search them quickly and accurately.

### An analogy: describing a person with numbers

Suppose you describe people with 3 numbers: `[kindness, humor, intelligence]` each from 0 to 10.

| Person | Kindness | Humor | Intelligence |
|--------|----------|-------|--------------|
| A      | 9        | 8     | 7            |
| B      | 8        | 9     | 7            |
| C      | 2        | 1     | 9            |

A and B are very similar (their number lists are almost the same). C is different. You didn't need words to see that; the numbers were enough.

Embedding models do the same thing for text, except:
- The "traits" (dimensions) are **not hand-picked by humans**. The model **learns** them.
- There are hundreds or thousands of them.
- Individual dimensions usually **don't have a human-readable meaning**. The *pattern* across all dimensions is what carries meaning.

---

## 2. Why We Need Embeddings

### The problem with keyword search

Traditional search (like SQL `LIKE`, or classic Lucene/Elasticsearch BM25) matches **words**.

| Query | Document | Keyword match? | Same meaning? |
|-------|----------|----------------|---------------|
| "cheap flights to Delhi" | "affordable air tickets to New Delhi" | Almost none | Yes |
| "python snake habitat" | "Python programming tutorial" | Yes ("python") | No |
| "my laptop won't turn on" | "device fails to power up" | None | Yes |

Keyword search fails because of:

- **Synonyms**: car/automobile, buy/purchase
- **Paraphrasing**: different sentence structure, same idea
- **Polysemy**: one word, many meanings (bank = river bank / money bank)
- **Language gaps**: query in Hindi, document in English (with multilingual models)
- **Vocabulary mismatch** in general: users rarely type the exact words the author used

### What embeddings give you

- **Semantic search**: retrieve by meaning
- **Clustering and deduplication**: group similar documents
- **Recommendations**: "more like this"
- **Classification**: feed vectors to a simple classifier
- **RAG**: give LLMs the right context from your private documents
- **Cross-lingual and cross-modal search**: text ↔ text in other languages, text ↔ images (with multimodal models)

---

## 3. A Short History: How Text Became Vectors

Understanding the evolution makes modern methods much easier to grasp.

### 3.1 One-hot encoding (the naive start)

Give every word in the vocabulary a position. Vocabulary size = 50,000 means each word is a 50,000-long vector with a single `1`.

```
cat → [0, 0, 1, 0, 0, ..., 0]
dog → [0, 0, 0, 0, 1, ..., 0]
```

**Problems:** enormous, sparse, and *every word is equally distant from every other word*. "cat" is as far from "dog" as from "refrigerator". There is no notion of meaning.

### 3.2 Bag of Words (BoW)

Represent a document as word counts.

```
Doc 1: "the cat sat on the mat"   →  {the:2, cat:1, sat:1, on:1, mat:1}
Doc 2: "the dog sat on the log"   →  {the:2, dog:1, sat:1, on:1, log:1}
```

**Problems:** ignores word order ("dog bites man" = "man bites dog"), ignores meaning, and common words dominate.

### 3.3 TF-IDF

**Term Frequency × Inverse Document Frequency** fixes the "common words dominate" problem.

```
TF(t, d)  = how often term t appears in document d
IDF(t)    = log( N / number of documents containing t )
TF-IDF    = TF × IDF
```

Rare words that appear often in *this* document get high scores. Words like "the" get near zero.

**Strengths:** fast, interpretable, still excellent for exact-term matching.
**Weakness:** still no understanding of meaning. Vectors are huge and sparse (one dimension per vocabulary word).

> BM25, the ranking function behind most keyword search engines, is a refined TF-IDF variant. It remains very relevant today (see [Hybrid Search](#12-hybrid-search-and-reranking)).

### 3.4 LSA / LSI (Latent Semantic Analysis)

Take the big TF-IDF matrix (documents × words) and compress it with **SVD** (Singular Value Decomposition) into, say, 300 dimensions. Words that co-occur across documents end up with similar compressed representations. This was the first widely used "dense semantic" representation. It's linear and limited, but the idea (compress into a dense space where co-occurrence = closeness) carried forward.

### 3.5 Word2Vec and GloVe (2013-2014): word embeddings

Key insight, from linguist J.R. Firth: *"You shall know a word by the company it keeps."*

**Word2Vec** trains a small neural network on a prediction task:
- **Skip-gram**: given a word, predict the words around it.
- **CBOW**: given the surrounding words, predict the middle word.

The learned weights become the word's vector. Famous result:

```
vector("king") - vector("man") + vector("woman") ≈ vector("queen")
```

**GloVe** achieves similar results by factorizing a global word co-occurrence matrix.

**Limitations:**
- **One vector per word**, regardless of context. "bank" has one vector for both river and money.
- To represent a document, you'd average the word vectors. This loses order and nuance.

### 3.5.1 Doc2Vec (Paragraph Vectors)

An extension of Word2Vec that learns an extra "document vector" alongside word vectors. Useful historically; largely superseded by transformers.

### 3.6 Contextual embeddings: ELMo → BERT (2018)

**ELMo** used bidirectional LSTMs to make word vectors depend on context. **BERT** used the Transformer architecture with *self-attention* so every token's vector is influenced by every other token in the sentence.

Now "bank" in "river bank" and "bank account" get **different vectors**.

But raw BERT wasn't built to produce good *sentence* vectors. Comparing two sentences required feeding both into the model together (a "cross-encoder"), which is too slow for searching millions of documents.

### 3.7 Sentence-BERT (2019) and modern embedding models

**Sentence-BERT (SBERT)** fine-tuned BERT in a "siamese" setup so that each sentence is encoded **independently** into a single vector, and similar sentences land close together. This is the **bi-encoder** pattern that powers modern semantic search:

- Encode all documents once, offline.
- Encode the query at search time.
- Compare vectors (very fast).

Since then, dedicated embedding models (E5, BGE, GTE, Instructor, Nomic Embed, OpenAI's `text-embedding-3-*`, Cohere Embed, Voyage, and others) trained on huge contrastive datasets have pushed quality much higher, with support for long inputs (thousands of tokens), many languages, and flexible output sizes.

### Summary timeline

| Era | Method | Dense? | Context-aware? | Doc-level meaning? |
|-----|--------|--------|----------------|--------------------|
| Pre-2000s | One-hot, BoW, TF-IDF | No (sparse) | No | Weak (word overlap) |
| 1990s-2000s | LSA | Yes | No | Moderate |
| 2013-2014 | Word2Vec, GloVe | Yes | No | Weak (averaged) |
| 2018 | BERT | Yes | Yes | Needs special pooling |
| 2019+ | SBERT, modern embedding models | Yes | Yes | **Strong** |

---

## 4. How a Modern Embedding Model Works (Step by Step)

Let's trace what happens when you embed the text:

> `"The cat sat on the mat."`

### Step 1: Tokenization

The text is split into **tokens** (pieces of words) using a learned vocabulary (WordPiece, BPE, SentencePiece, etc.).

```
"The cat sat on the mat."
→ ["[CLS]", "the", "cat", "sat", "on", "the", "mat", ".", "[SEP]"]
→ token IDs: [101, 1996, 4937, 2938, 2006, 1996, 13523, 1012, 102]
```

Rare words are broken into subwords: `"unbelievably"` → `["un", "##believ", "##ably"]`. This means the model never faces a truly unknown word.

Special tokens like `[CLS]` (start) and `[SEP]` (separator) are added by some models.

**Why it matters:** Models have a **maximum token length** (e.g., 512 tokens for many; 8,192 or more for newer long-context embedders). Text beyond the limit is **silently truncated** by many libraries. This is a major reason chunking matters.

### Step 2: Token embedding lookup

Each token ID is mapped to a learned vector via an **embedding table** (a big matrix of size `vocab_size × hidden_dim`).

```
token ID 4937 ("cat") → [0.12, -0.45, 0.33, ... ]   (hidden_dim numbers, e.g. 768)
```

At this point "cat" has the same vector no matter what sentence it's in.

### Step 3: Add positional information

Transformers process all tokens in parallel and have no built-in sense of order. So position information is injected, via:

- **Learned absolute position embeddings** (original BERT), or
- **Sinusoidal encodings** (original Transformer), or
- **Rotary position embeddings (RoPE)** or **ALiBi** (common in newer models, better for long inputs).

Now the model knows "cat" is the 3rd token and "mat" is the 7th.

### Step 4: Transformer layers (self-attention + feed-forward)

This is where context enters. The token vectors pass through a stack of N identical layers (e.g., 6, 12, 24).

**Each layer has two main parts:**

#### (a) Self-attention

For every token, the model asks: *"Which other tokens in this text should I pay attention to in order to understand myself better?"*

Each token vector is projected into three vectors:
- **Query (Q)**: "what am I looking for?"
- **Key (K)**: "what do I offer?"
- **Value (V)**: "what information do I carry?"

```
Attention(Q, K, V) = softmax( Q · Kᵀ / √d_k ) · V
```

In plain words:
1. Compare each token's Query with every token's Key (dot product) → relevance scores.
2. Scale and apply softmax → scores become weights that sum to 1.
3. Take a weighted average of all Value vectors → the token's new, context-enriched vector.

Example: in "The bank of the river was muddy", the token "bank" attends strongly to "river", pulling its vector toward the geography meaning. In "The bank approved my loan", it attends to "loan" and "approved" instead.

**Multi-head attention** runs this several times in parallel (e.g., 12 heads), each learning to focus on different kinds of relationships (syntax, coreference, topic, etc.), then concatenates the results.

#### (b) Feed-forward network (FFN)

A small two-layer neural network applied independently to each token vector. It transforms and refines the representation (this is where much of the model's "knowledge" is stored).

Both parts are wrapped with **residual connections** (add the input back to the output) and **layer normalization** (keep numbers stable). These make deep stacks trainable.

After N layers, every token has a **contextual vector**: its meaning *in this sentence*.

### Step 5: Pooling (many token vectors → ONE document vector)

We have one vector per token, but want a single vector for the whole text. Common strategies:

| Pooling | How it works | Used by |
|---------|--------------|---------|
| **Mean pooling** | Average all token vectors (ignoring padding) | SBERT, E5, GTE, many others |
| **CLS pooling** | Use the vector of the special `[CLS]` token as the summary | BGE and others |
| **Max pooling** | Take the max across tokens per dimension | Less common |
| **Last-token pooling** | Use the final token's vector (decoder-style models) | LLM-based embedders |
| **Weighted-mean pooling** | Later tokens weighted more (decoder-style models) | SGPT and similar |

Mean pooling in code:

```python
# token_embeddings: [seq_len, hidden_dim]; attention_mask: [seq_len] (1 = real token, 0 = padding)
mask = attention_mask.unsqueeze(-1)                  # [seq_len, 1]
summed = (token_embeddings * mask).sum(dim=0)        # [hidden_dim]
count = mask.sum(dim=0).clamp(min=1e-9)              # [1]
doc_vector = summed / count                          # [hidden_dim]
```

**Important:** Always use the pooling method the model was trained with. Using the wrong one degrades quality.

### Step 6: Optional projection and normalization

- Some models add a **linear projection** layer to change the output size.
- Most apply **L2 normalization** so the vector has length 1:

```
v_normalized = v / ||v||₂
```

With unit-length vectors, **dot product = cosine similarity**, which makes search faster and simpler.

### Final result

```
"The cat sat on the mat."  →  [0.031, -0.087, 0.142, ..., 0.019]   # e.g. 384 / 768 / 1024 / 1536 / 3072 numbers
```

### Bi-encoder vs Cross-encoder (important distinction)

| | Bi-encoder (embedding model) | Cross-encoder (reranker) |
|---|---|---|
| Input | One text at a time | Query + document **together** |
| Output | A vector per text | A single relevance score |
| Document precomputation | Yes, offline | No, must run per (query, doc) pair |
| Speed | Very fast at search time | Slow |
| Accuracy | Good | Better |
| Use | **First-stage retrieval** over millions | **Reranking** the top 20-100 results |

Production systems typically use both: bi-encoder to shortlist, cross-encoder to polish. See [Section 12](#12-hybrid-search-and-reranking).

### Encoder-only vs LLM-based embedding models

- **Encoder-only** (BERT-family): bidirectional attention, small and fast (22M-500M params). The workhorse for years.
- **LLM-based embedders** (decoder models fine-tuned for embeddings): larger (1B-8B+ params), often top the leaderboards, handle long context and instructions well, but cost more to run.

---

## 5. How Embedding Models Are Trained

The training goal is simple to state:

> **Make vectors of related texts close, and vectors of unrelated texts far.**

### 5.1 Training data: pairs of related texts

Examples of "positive pairs":
- (question, answer passage)
- (search query, clicked document)
- (title, article body)
- (sentence, its paraphrase)
- (code comment, code)
- (translated sentence pairs, for multilingual models)
- (anchor, entailed sentence) from natural language inference datasets

Modern models are first **pre-trained on billions of weakly supervised pairs** (e.g., web-scraped title/body, Reddit question/answer, Wikipedia sections) and then **fine-tuned on smaller, higher-quality labeled datasets**, often with *hard negatives*.

### 5.2 Contrastive learning and InfoNCE loss

For a batch of B pairs `(q_i, d_i)`, each query's own document is the **positive**; all other documents in the batch are **in-batch negatives**.

The model computes similarity between every query and every document in the batch, forming a B×B matrix, and the loss pushes the diagonal (correct pairs) to be highest:

```
L = - (1/B) Σᵢ log [ exp( sim(qᵢ, dᵢ) / τ ) / Σⱼ exp( sim(qᵢ, dⱼ) / τ ) ]
```

- `sim` is usually cosine similarity.
- `τ` (temperature) is a small number (e.g., 0.01-0.05) that sharpens the distribution.

In plain words: *"Among all documents in this batch, the true match should win the popularity contest for this query."*

**Bigger batches = more negatives = better embeddings** (which is why training uses large batches or tricks like gradient caching).

### 5.3 Hard negatives

Random negatives are easy ("quantum physics" vs "pizza recipe"). The model learns more from **hard negatives**: documents that look relevant but aren't (e.g., mined by retrieving top results with an existing model and removing true positives). They teach the model fine distinctions.

### 5.4 Instruction and prefix tuning

Many modern models expect a **task prefix**, because "query" and "document" are different kinds of text:

```
E5 style:    "query: how to reset password"      vs   "passage: To reset your password, go to..."
BGE style:   "Represent this sentence for searching relevant passages: ..." (for queries only)
```

**Always check the model card.** Forgetting a required prefix quietly hurts results.

### 5.5 Matryoshka Representation Learning (MRL)

Newer models are trained so that the **first k dimensions of the vector are themselves a valid, smaller embedding** (like Russian nesting dolls). You can truncate a 3072-dim vector to 1024, 512, or 256 dims (and re-normalize) with modest quality loss, saving storage and compute.

### 5.6 Distillation

Smaller, faster models are often trained to mimic larger ones (or a cross-encoder's scores), getting much of the accuracy at a fraction of the cost.

---

## 6. Measuring Similarity

Once you have two vectors **a** and **b**, how do you measure "closeness"?

### 6.1 Cosine similarity (the default)

Measures the **angle** between vectors, ignoring their length.

```
cosine(a, b) = (a · b) / (||a|| × ||b||)
```

- **1.0** → same direction (very similar)
- **0.0** → perpendicular (unrelated)
- **-1.0** → opposite direction

```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

Why angle and not distance? Text length can change a vector's magnitude without changing its topic. Angle captures *direction of meaning*.

### 6.2 Dot product (inner product)

```
a · b = Σ aᵢ × bᵢ
```

- For **normalized** vectors, identical to cosine similarity (and cheaper).
- For un-normalized vectors, magnitude influences the score. Some models are trained specifically for dot product, so follow the model card.

### 6.3 Euclidean (L2) distance

Straight-line distance:

```
d(a, b) = √( Σ (aᵢ - bᵢ)² )
```

Smaller = more similar. For normalized vectors, L2 distance and cosine similarity give the **same ranking**:

```
||a - b||² = 2 - 2 · cosine(a, b)     (when ||a|| = ||b|| = 1)
```

### 6.4 Others

- **Manhattan (L1) distance**: sum of absolute differences.
- **Hamming distance**: used for binary-quantized vectors (count differing bits), extremely fast.
- **Jaccard**: for sets/sparse binary vectors.

### Quick guide

| Situation | Use |
|-----------|-----|
| Don't know / default | **Cosine** |
| Vectors already normalized | **Dot product** (fastest, equivalent to cosine) |
| Model card says L2 | L2 |
| Binary embeddings | Hamming |

**Rule:** Use the **same metric the model was trained with** and the **same metric configured in your vector index**.

### A note on interpreting scores

A cosine score of 0.8 does **not** mean "80% similar." Score distributions vary by model: some models produce scores between 0.6-0.9 for everything, others spread between 0 and 1. Scores are good for **ranking**; thresholds must be **calibrated empirically** on your own data.

---

## 7. The Document Embedding Pipeline

Here's the full journey from raw files to a searchable system.

```
┌────────────┐   ┌───────────┐   ┌──────────┐   ┌───────────┐   ┌──────────────┐
│ 1. Ingest  │ → │ 2. Clean  │ → │ 3. Chunk │ → │ 4. Embed  │ → │ 5. Store +   │
│ PDFs, HTML │   │ & parse   │   │ split    │   │ model →   │   │    Index     │
│ DB, Docs   │   │ metadata  │   │ text     │   │ vectors   │   │ (vector DB)  │
└────────────┘   └───────────┘   └──────────┘   └───────────┘   └──────────────┘

QUERY TIME:
┌──────────┐   ┌───────────┐   ┌─────────────┐   ┌──────────┐   ┌───────────┐
│ User     │ → │ Embed the │ → │ ANN search  │ → │ (Rerank) │ → │ Results / │
│ question │   │ query     │   │ top-k chunks│   │          │   │ LLM prompt│
└──────────┘   └───────────┘   └─────────────┘   └──────────┘   └───────────┘
```

### Step 1: Ingestion

Load documents from PDFs, Word files, HTML pages, Markdown, Notion/Confluence, databases, emails, code repos, etc.

### Step 2: Parsing and cleaning

- Extract text (PDF extraction and OCR can be messy: headers, footers, page numbers, broken tables).
- Remove boilerplate (nav menus, cookie banners, repeated footers).
- Normalize whitespace and encoding.
- **Preserve structure** (headings, lists, tables) where you can. Structure is valuable for chunking.
- Capture **metadata**: source URL, title, author, date, section, language, access permissions, document ID.

> Garbage in, garbage out. Parsing quality often matters more than which embedding model you choose.

### Step 3: Chunking

Embedding models have a token limit, and, more importantly, **one vector can only capture so much meaning**. A 50-page document squeezed into one vector becomes a blurry average of everything. So documents are split into **chunks**. See [the next section](#8-chunking-strategies-in-depth).

### Step 4: Embedding

Send each chunk through the embedding model (in batches, for efficiency, ideally on a GPU or via an API). Store the resulting vector alongside the chunk text and metadata.

### Step 5: Storage and indexing

Insert `(id, vector, chunk_text, metadata)` into a vector database or a database with vector support, and build an ANN index for fast search.

### Query time

1. Embed the user's query with the **same model** (with the correct query prefix, if any).
2. Search the index for the top-k nearest chunk vectors (optionally filtered by metadata).
3. Optionally rerank.
4. Return results, or feed chunks into an LLM for answer generation (RAG).

---

## 8. Chunking Strategies in Depth

Chunking is **the most underrated factor** in retrieval quality.

### Why chunk at all?

1. **Model token limits**: input beyond the max is truncated and lost.
2. **Specificity**: a vector for a focused 300-word passage matches focused questions better than a vector for a whole book.
3. **LLM context cost**: retrieving small relevant pieces is cheaper and more precise than stuffing whole documents into a prompt.

### The tradeoff

| Chunk too small | Chunk too large |
|-----------------|-----------------|
| Loses context ("It was approved." - what was?) | Vector becomes a vague average |
| Too many vectors (more cost) | Irrelevant text dilutes the match |
| Fragmented answers | Wastes LLM context window |

### Common strategies

#### 8.1 Fixed-size chunking
Split every N tokens/characters (e.g., 500 tokens) with some **overlap** (e.g., 50-100 tokens).

- ✅ Simple, predictable.
- ❌ Cuts mid-sentence or mid-idea.

#### 8.2 Recursive character/text splitting
Try to split on the largest natural separator first (paragraphs `\n\n`), then lines `\n`, then sentences, then words, until pieces fit the size limit. (Popular in LangChain/LlamaIndex.)

- ✅ Good default; respects natural boundaries.

#### 8.3 Sentence-based chunking
Group whole sentences until a size limit is reached.

#### 8.4 Structure-aware chunking
Use document structure: split by Markdown headings, HTML tags, PDF sections, code functions/classes, table rows. Keep the **heading hierarchy** as context.

- ✅ Best for manuals, docs, legal text, and code.

#### 8.5 Semantic chunking
Embed sentences, then start a new chunk where similarity between adjacent sentences drops sharply (topic shift).

- ✅ Topic-coherent chunks.
- ❌ Extra compute; results vary.

#### 8.6 Hierarchical / parent-child ("small-to-big")
Index **small chunks** for precise matching, but when one matches, return its **larger parent** section (or neighboring chunks) as context.

- ✅ Precision of small chunks + context of large ones.

#### 8.7 Late chunking
With long-context embedding models, run the whole document through the transformer first (so every token sees full-document context), *then* pool token vectors per chunk. Each chunk vector keeps document-level context.

#### 8.8 Contextual chunk enrichment
Prepend a short generated summary or the document title/section path to each chunk before embedding, e.g.:

```
[Document: HR Policy 2025 > Section: Leave > Sub: Maternity]
Employees are eligible for 26 weeks of paid leave...
```

This helps isolated chunks stay understandable ("contextual retrieval" style techniques can substantially reduce failed retrievals).

#### 8.9 Proposition / LLM-based chunking
Use an LLM to rewrite a passage into self-contained factual statements. Very precise but costly.

### Practical starting points

| Content type | Suggested start |
|--------------|-----------------|
| General prose, articles | 200-500 tokens, 10-20% overlap, recursive splitter |
| Technical docs / Markdown | Split by headings; cap at 300-800 tokens |
| FAQs | One Q&A pair per chunk |
| Code | By function/class, include file path and signature |
| Legal / contracts | By clause/section, keep numbering and titles |
| Tables | Row-wise or table-wise with header repeated |
| Chat/transcripts | By speaker turns or time windows |

> These are starting points, not rules. **Tune on your own data using a retrieval evaluation set** (see [Section 14](#14-evaluating-retrieval-quality)).

### Overlap: why and how much?

Overlap prevents an answer that straddles a boundary from being cut in half. 10-20% is typical. More overlap = better recall but more storage and duplicate results (consider deduplicating at query time).

### Always store metadata with each chunk

```json
{
  "chunk_id": "doc42_chunk_07",
  "doc_id": "doc42",
  "title": "Refund Policy",
  "section": "International Orders",
  "position": 7,
  "source_url": "https://example.com/refunds",
  "updated_at": "2026-03-14",
  "language": "en",
  "acl": ["support-team"]
}
```

Metadata enables **filtering** (by date, tenant, permissions), **citations**, and **neighbor expansion**.

---

## 9. Searching Vectors Fast: ANN Algorithms

### The scale problem

**Exact (brute-force) k-NN**: compare the query against *every* vector.

- 1 million vectors × 768 dims → ~768 million multiply-adds per query. Fine.
- 1 billion vectors → far too slow and memory-hungry.

**Approximate Nearest Neighbor (ANN)** algorithms trade a tiny amount of accuracy (maybe finding 95-99% of the true nearest neighbors) for **massive** speedups (10x-1000x).

> The metric for ANN quality is **recall@k**: of the true top-k neighbors, what fraction did the ANN index return?

### 9.1 Flat index (exact)

Store vectors in an array; scan all of them.

- ✅ 100% recall, simple. Good up to roughly hundreds of thousands to a few million vectors (especially with SIMD/GPU).
- ❌ Doesn't scale linearly forever.

### 9.2 HNSW (Hierarchical Navigable Small World): the most popular

Builds a **multi-layer graph** where each vector is a node connected to nearby nodes.

**Intuition: a highway system for search.**

```
Layer 2 (sparse):    A ─────────────── F                   ← "interstate highways": long jumps
Layer 1 (medium):    A ──── C ──── E ─ F ──── H            ← "state highways"
Layer 0 (dense):     A─B─C─D─E─F─G─H─I─J─K─L               ← "local streets": all vectors
```

**Search:**
1. Enter at the top layer at a fixed entry point.
2. Greedily hop to the neighbor closest to the query until no closer neighbor exists.
3. Drop down one layer, continue from that point.
4. At layer 0, explore a wider candidate list and return the best k.

**Insertion:** Each new vector is assigned a random maximum layer (exponentially decaying probability, so few nodes are in upper layers), then connected to its nearest neighbors on each layer.

**Key parameters:**

| Parameter | Meaning | Effect |
|-----------|---------|--------|
| `M` | Max connections per node | Higher → better recall, more memory, slower build |
| `efConstruction` | Candidate list size during build | Higher → better graph quality, slower build |
| `efSearch` (`ef`) | Candidate list size during search | Higher → better recall, slower queries |

- ✅ Excellent speed/recall; supports incremental inserts; widely supported (pgvector, Qdrant, Weaviate, Milvus, Elasticsearch, OpenSearch, FAISS...).
- ❌ **Memory-hungry** (graph + vectors usually kept in RAM); deletes are awkward; build can be slow for huge datasets.

### 9.3 IVF (Inverted File Index)

**Intuition: a library organized by sections.**

1. **Training:** Run **k-means** on a sample of vectors to find `nlist` cluster centroids (e.g., 1,024).
2. **Indexing:** Assign each vector to its nearest centroid; store it in that centroid's "inverted list."
3. **Search:** Compare the query to centroids, pick the closest `nprobe` clusters (e.g., 8-32), and only scan vectors in those clusters.

| Parameter | Effect |
|-----------|--------|
| `nlist` | Number of clusters. Rule of thumb: ~√N to 4√N |
| `nprobe` | Clusters searched. Higher → better recall, slower |

- ✅ Lower memory than HNSW, fast to build, good for big data.
- ❌ Recall depends on cluster quality; needs a training step; vectors near cluster borders can be missed (raise `nprobe`).

### 9.4 Product Quantization (PQ): compressing vectors

Shrinks vectors dramatically so billions fit in memory.

1. Split each D-dim vector into `m` sub-vectors (e.g., 768 dims → 96 sub-vectors of 8 dims).
2. For each sub-space, run k-means to build a **codebook** of 256 centroids.
3. Replace each sub-vector with the **1-byte ID** of its nearest centroid.

A 768-dim float32 vector (3,072 bytes) becomes ~96 bytes. That's **~32× smaller**. Distances are approximated using precomputed lookup tables.

- ✅ Huge memory savings.
- ❌ Lossy; lower accuracy. Often combined: **IVF-PQ**, then **rerank the top candidates with full-precision vectors**.

### 9.5 Scalar and binary quantization

- **Scalar quantization (SQ8)**: store each float32 as int8 → 4× smaller, tiny quality loss.
- **Binary quantization**: keep only the sign of each dimension (1 bit) → **32× smaller**, compared with ultra-fast Hamming distance. Works well with high-dimensional modern models, especially when followed by a rescoring step with full vectors.

### 9.6 LSH (Locality-Sensitive Hashing)

Hash functions designed so similar vectors collide in the same bucket with high probability. Conceptually elegant and used historically; generally outperformed by graph and IVF methods for dense embeddings today.

### 9.7 DiskANN / Vamana, SPANN, ScaNN

- **DiskANN**: graph-based index designed to live mostly on **SSD**, keeping memory use low while serving billion-scale search.
- **ScaNN** (Google): anisotropic quantization optimized for maximum inner product search.
- **SPANN**: partition-based, hybrid memory/disk.

### Comparison

| Algorithm | Speed | Recall | Memory | Build time | Updates | Best for |
|-----------|-------|--------|--------|------------|---------|----------|
| Flat | Slow at scale | 100% | High | None | Trivial | < ~1M vectors, ground truth |
| HNSW | Very fast | Very high | High | Medium-slow | Good (inserts) | Most apps; low-latency search |
| IVF | Fast | Good | Medium | Fast | Needs retrain over time | Large datasets |
| IVF-PQ | Fast | Moderate | **Low** | Medium | Needs retrain | Huge datasets, tight memory |
| DiskANN | Fast | High | Low (SSD) | Slow | Moderate | Billion-scale |

### Filtering with ANN: a subtle problem

Real queries often include filters: *"find similar documents, but only from tenant 7, published after 2025."*

- **Post-filtering**: search first, then filter → may return too few results.
- **Pre-filtering**: filter first, then search → can break graph connectivity or be slow.
- **Filtered/in-graph search**: modern databases integrate filters into the traversal (varies by engine). Test the behavior of your engine with selective filters.

---

## 10. Vector Databases and Storage

### What does a vector database provide?

- Storage for vectors + payload/metadata
- ANN indexes (HNSW, IVF, etc.)
- Filtering, hybrid (keyword + vector) search
- CRUD operations, persistence, replication, sharding
- Scalability, multi-tenancy, access control

### Options (non-exhaustive)

| Type | Examples | Notes |
|------|----------|-------|
| Libraries | FAISS, hnswlib, Annoy, ScaNN | In-process; you manage persistence and serving |
| Purpose-built DBs | Qdrant, Weaviate, Milvus, Pinecone, Chroma | Rich vector features, filtering, scaling |
| Extensions to existing DBs | **pgvector** (PostgreSQL), Elasticsearch/OpenSearch kNN, MongoDB Atlas Vector Search, Redis vector search | Keep vectors next to your relational/doc data |
| Cloud-native | Managed offerings on major clouds | Operational convenience |

### How to choose

- **Already on PostgreSQL and < ~10M vectors?** pgvector is often enough: one system, transactions, SQL joins, simpler operations.
- **Need massive scale, advanced filtering, or specialized performance?** A purpose-built vector database.
- **Prototyping?** Chroma, FAISS, or an in-memory index.
- **Need strong keyword + vector in one engine?** Elasticsearch/OpenSearch, Weaviate, Qdrant (with sparse vectors), etc.

### Storage math

```
bytes per vector = dimensions × bytes_per_value
float32:  4 bytes     float16: 2 bytes     int8: 1 byte     binary: 1/8 byte
```

Example: **10 million chunks × 1536 dims × 4 bytes ≈ 61 GB** just for raw vectors, before index overhead (HNSW graph can add significant extra) and text/metadata. Quantization or Matryoshka truncation can cut this drastically.

### pgvector example (SQL)

```sql
-- Enable the extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for chunks
CREATE TABLE doc_chunks (
  id          BIGSERIAL PRIMARY KEY,
  doc_id      TEXT NOT NULL,
  chunk_index INT  NOT NULL,
  content     TEXT NOT NULL,
  metadata    JSONB DEFAULT '{}',
  embedding   VECTOR(768)       -- must match your model's dimension
);

-- HNSW index using cosine distance
CREATE INDEX ON doc_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Query: top 5 most similar chunks
-- <=> is cosine distance (1 - cosine similarity); $1 is the query embedding
SELECT id, doc_id, content,
       1 - (embedding <=> $1) AS cosine_similarity
FROM doc_chunks
WHERE metadata->>'language' = 'en'
ORDER BY embedding <=> $1
LIMIT 5;

-- Tune recall/speed at query time
SET hnsw.ef_search = 100;
```

Operators in pgvector: `<->` L2 distance, `<=>` cosine distance, `<#>` negative inner product.

---

## 11. Retrieval-Augmented Generation (RAG)

LLMs know a lot, but not **your private data**, nor anything after their training cutoff, and they sometimes hallucinate. RAG fixes this by retrieving relevant documents at question time and giving them to the LLM as context.

### The RAG flow

```
User question
     │
     ▼
 Embed question ──► Vector search (+ keyword, filters) ──► Top-k chunks
                                                              │
                                                              ▼
                                  ┌──────────────────────────────────────────┐
                                  │ Prompt:                                  │
                                  │ "Answer using ONLY the context below.    │
                                  │  If it's not there, say you don't know.  │
                                  │  Context: [chunk1] [chunk2] [chunk3]     │
                                  │  Question: ..."                          │
                                  └──────────────────────────────────────────┘
                                                              │
                                                              ▼
                                                    LLM → Grounded answer + citations
```

### Why RAG works well

- Answers grounded in your actual documents (with citations)
- No retraining when documents change, just re-index
- Respects per-user permissions via metadata filters
- Cheaper than fine-tuning for knowledge injection

### Where RAG fails (and what to do)

| Failure | Cause | Fix |
|---------|-------|-----|
| Right doc exists but isn't retrieved | Bad chunking, weak model, vocabulary mismatch | Better chunking, hybrid search, query rewriting, better model |
| Retrieved chunks are off-topic | Weak embeddings, chunks too large | Smaller chunks, reranker |
| Answer ignores retrieved context | Prompting, too much noise in context | Stronger instructions, fewer/better chunks |
| Multi-hop questions fail | Needed facts live in different chunks | Iterative/agentic retrieval, query decomposition |
| Stale answers | Index not refreshed | Incremental ingestion pipeline |
| Question and answer phrased very differently | Query-document asymmetry | HyDE, query rewriting, instruction-tuned embeddings |

### Useful RAG enhancements

- **Query rewriting / expansion**: have an LLM rephrase or split complex questions.
- **HyDE (Hypothetical Document Embeddings)**: have an LLM write a *hypothetical answer*, embed that, and search with it (answers resemble documents more than questions do).
- **Multi-query retrieval**: generate several paraphrases, retrieve for each, merge results.
- **Neighbor expansion**: include chunks adjacent to matched chunks.
- **Metadata-aware retrieval**: let the LLM extract filters (dates, product names) from the question.
- **Citation and source tracking**: return doc IDs/URLs with each answer.

---

## 12. Hybrid Search and Reranking

### Why hybrid?

| Dense (embeddings) | Sparse (BM25 / keyword) |
|--------------------|-------------------------|
| Understands meaning, synonyms, paraphrases | Exact term matching |
| Weak on rare identifiers, SKUs, error codes, names | Great for IDs, jargon, exact phrases |
| "Fuzzy" | Precise |

Queries like `"error ORA-00942"` or `"policy HR-204"` are best served by keywords. Queries like `"how do I get time off after having a baby"` need semantics. **Combine them.**

### Fusing the results: Reciprocal Rank Fusion (RRF)

Run both searches; merge using ranks (not raw scores, which aren't comparable):

```
RRF_score(doc) = Σ over each ranker r of  1 / (k + rank_r(doc))      (k is typically 60)
```

```python
def rrf(rankings, k=60):
    """rankings: list of lists of doc_ids, each ordered best → worst."""
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)
```

Alternatively: weighted score combination after normalization.

### Learned sparse retrieval

Models like **SPLADE** produce sparse vectors with learned term expansion (so "car" activates "automobile" too) and can be served from inverted indexes. A middle path between BM25 and dense.

### Multi-vector / late interaction (ColBERT)

Instead of one vector per document, keep **one vector per token** and compute similarity as the sum of each query token's best match across document tokens ("MaxSim"). Higher accuracy and better fine-grained matching, at the cost of much more storage. Useful in high-precision scenarios.

### Reranking

Two-stage retrieval is the standard high-quality recipe:

1. **Stage 1 (recall)**: bi-encoder and/or BM25 retrieves top 50-200 candidates cheaply.
2. **Stage 2 (precision)**: a **cross-encoder reranker** scores each (query, candidate) pair jointly and reorders; keep top 3-10.

Rerankers see the query and passage *together* with full cross-attention, which catches subtle relevance that independent vectors miss. They're slower (hence only applied to a shortlist) but often yield the single biggest quality jump in a retrieval system.

---

## 13. Hands-On Code Examples

### 13.1 Minimal example with `sentence-transformers`

```bash
pip install sentence-transformers numpy
```

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 1. Load a model (384-dim, small and fast)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 2. Your documents
docs = [
    "How to reset your account password",
    "Steps to recover a forgotten login credential",
    "Best recipes for vegetarian dinner",
    "Quarterly revenue grew by 12 percent",
    "Fixing a flat bicycle tire at home",
]

# 3. Embed (normalize so dot product == cosine similarity)
doc_vecs = model.encode(docs, normalize_embeddings=True)    # shape: (5, 384)

# 4. Embed the query and search
query = "I can't log in, how do I get my password back?"
q_vec = model.encode(query, normalize_embeddings=True)       # shape: (384,)

scores = doc_vecs @ q_vec                                    # cosine similarities
for idx in np.argsort(-scores):
    print(f"{scores[idx]:.3f}  {docs[idx]}")
```

Typical output: the two password/login documents rank at the top, even though they share few words with the query.

### 13.2 TF-IDF from scratch (to understand the "old way")

```python
import math
from collections import Counter

docs = [
    "the cat sat on the mat",
    "the dog sat on the log",
    "cats and dogs are pets",
]
tokenized = [d.split() for d in docs]
vocab = sorted({w for d in tokenized for w in d})
N = len(docs)

def idf(term):
    df = sum(1 for d in tokenized if term in d)
    return math.log((N + 1) / (df + 1)) + 1     # smoothed IDF

def tfidf_vector(tokens):
    counts = Counter(tokens)
    return [counts[t] / len(tokens) * idf(t) for t in vocab]

vectors = [tfidf_vector(d) for d in tokenized]   # sparse, vocab-sized vectors
```

### 13.3 Chunking function (recursive, with overlap)

```python
def chunk_text(text, max_chars=1200, overlap=150):
    """Simple paragraph-aware chunker with character overlap."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""

    for para in paragraphs:
        # If a single paragraph is too long, split it by sentences/words
        pieces = [para] if len(para) <= max_chars else split_long(para, max_chars)
        for piece in pieces:
            if len(current) + len(piece) + 2 <= max_chars:
                current = f"{current}\n\n{piece}".strip()
            else:
                if current:
                    chunks.append(current)
                tail = current[-overlap:] if current else ""
                current = f"{tail}\n\n{piece}".strip() if tail else piece
    if current:
        chunks.append(current)
    return chunks

def split_long(text, max_chars):
    words, out, buf = text.split(), [], ""
    for w in words:
        if len(buf) + len(w) + 1 > max_chars:
            out.append(buf); buf = w
        else:
            buf = f"{buf} {w}".strip()
    if buf:
        out.append(buf)
    return out
```

(In production, measure size in **tokens** using the model's tokenizer, not characters.)

### 13.4 FAISS: fast similarity search

```bash
pip install faiss-cpu
```

```python
import faiss
import numpy as np

d = doc_vecs.shape[1]                       # embedding dimension

# Exact search with inner product (== cosine for normalized vectors)
index = faiss.IndexFlatIP(d)
index.add(doc_vecs.astype("float32"))

D, I = index.search(q_vec.reshape(1, -1).astype("float32"), k=3)
print(I[0], D[0])                           # ids and similarity scores

# Approximate search with HNSW
hnsw = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)   # M = 32
hnsw.hnsw.efConstruction = 200
hnsw.add(doc_vecs.astype("float32"))
hnsw.hnsw.efSearch = 64
D, I = hnsw.search(q_vec.reshape(1, -1).astype("float32"), k=3)
```

### 13.5 End-to-end with PostgreSQL + pgvector (Python)

```python
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-base-en-v1.5")        # 768 dims
conn = psycopg.connect("postgresql://user:pass@localhost/mydb")
register_vector(conn)

def index_chunks(doc_id, chunks):
    vecs = model.encode(chunks, normalize_embeddings=True, batch_size=32)
    with conn.cursor() as cur:
        for i, (text, vec) in enumerate(zip(chunks, vecs)):
            cur.execute(
                "INSERT INTO doc_chunks (doc_id, chunk_index, content, embedding) "
                "VALUES (%s, %s, %s, %s)",
                (doc_id, i, text, vec),
            )
    conn.commit()

def search(query, k=5):
    # BGE recommends a query instruction for retrieval
    q = model.encode(
        "Represent this sentence for searching relevant passages: " + query,
        normalize_embeddings=True,
    )
    with conn.cursor() as cur:
        cur.execute(
            "SELECT doc_id, content, 1 - (embedding <=> %s) AS score "
            "FROM doc_chunks ORDER BY embedding <=> %s LIMIT %s",
            (q, q, k),
        )
        return cur.fetchall()
```

### 13.6 Using a hosted embedding API (Node.js sketch)

```javascript
// Pseudocode-style example: most providers follow this pattern.
// Replace the URL, model name and auth header per provider docs.
async function embed(texts) {
  const res = await fetch("https://api.example.com/v1/embeddings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.EMBEDDING_API_KEY}`,
    },
    body: JSON.stringify({ model: "your-embedding-model", input: texts }),
  });
  const json = await res.json();
  return json.data.map((d) => d.embedding); // array of float arrays
}

function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}
```

Tips for API usage: **batch** inputs, handle **rate limits** with retries/backoff, **cache** embeddings by content hash, and record the **model name/version** with every stored vector.

### 13.7 Visualizing embeddings (intuition builder)

```python
from sklearn.manifold import TSNE        # or umap-learn for UMAP
import matplotlib.pyplot as plt

coords = TSNE(n_components=2, perplexity=5, random_state=42).fit_transform(doc_vecs)
plt.scatter(coords[:, 0], coords[:, 1])
for (x, y), label in zip(coords, docs):
    plt.annotate(label[:25], (x, y))
plt.show()
```

Related documents appear as clusters. (Treat t-SNE/UMAP plots as intuition aids, not precise measurements; distances are distorted by the 2D projection.)

---

## 14. Evaluating Retrieval Quality

"It seems to work" is not enough. Build a small evaluation set.

### 14.1 Build a test set

Collect **50-500 realistic queries**, each paired with the chunk(s)/document(s) that should be retrieved ("ground truth"). Sources:
- Real user queries/search logs
- Questions written by domain experts
- LLM-generated questions from chunks (then human-reviewed)

### 14.2 Metrics

| Metric | Question it answers |
|--------|---------------------|
| **Recall@k** | Of the relevant items, how many appear in the top k? |
| **Precision@k** | Of the top k results, how many are relevant? |
| **MRR** (Mean Reciprocal Rank) | How high is the *first* relevant result? `1/rank`, averaged |
| **nDCG@k** | Are the *most* relevant results ranked highest? (supports graded relevance) |
| **Hit rate@k** | Did at least one relevant result appear in the top k? |

```python
def recall_at_k(retrieved_ids, relevant_ids, k):
    top = set(retrieved_ids[:k])
    return len(top & set(relevant_ids)) / max(len(relevant_ids), 1)

def mrr(retrieved_ids, relevant_ids):
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / rank
    return 0.0
```

### 14.3 Separate retrieval from generation

For RAG, evaluate **retrieval** (above) *and* **generation** (faithfulness to context, answer correctness, citation accuracy, hallucination rate) independently, so you know which stage is failing. Tools like RAGAS, TruLens, and DeepEval help; LLM-as-judge evaluations are common but should be spot-checked by humans.

### 14.4 Benchmarks for choosing models

- **MTEB** (Massive Text Embedding Benchmark) and its multilingual variants: public leaderboard across retrieval, clustering, classification, etc.
- **BEIR**: retrieval benchmark across many domains.

> Leaderboards are a good *shortlist* tool, but results on **your** data matter more. Domain-specific text (legal, medical, code, Hindi/Indic languages, etc.) can behave differently. Always test 2-4 candidate models on your own evaluation set.

### 14.5 ANN-specific evaluation

Compare ANN results to exact (flat) search on a sample to measure **recall of the index** itself, then tune `efSearch` / `nprobe` to hit your target (commonly 95-99% recall) at acceptable latency.

---

## 15. Choosing a Model and Tuning Dimensions

### Criteria checklist

| Factor | Questions to ask |
|--------|-----------------|
| **Quality** | MTEB score in the relevant task and *your* eval set results |
| **Language** | English-only vs multilingual vs specific Indic/other languages |
| **Domain** | General vs code vs legal/medical/finance |
| **Max input length** | 512 tokens? 8k? Does it match your chunk sizes? |
| **Dimensions** | Affects storage, RAM, and latency |
| **Latency/throughput** | Self-hosted GPU/CPU vs API; batch speed |
| **Cost** | Per-token API pricing vs infrastructure cost |
| **Licensing** | Open weights (commercial use allowed?) vs proprietary API |
| **Privacy/compliance** | Can data leave your environment? |
| **Features** | Matryoshka, instruction prefixes, quantization-aware, multi-vector, sparse output |

### Open-source vs API

| | Open-source/self-hosted | Hosted API |
|--|------------------------|------------|
| Setup | You run the model (GPU/CPU) | Call an endpoint |
| Data privacy | Full control | Data goes to a provider |
| Cost at scale | Fixed infra; cheaper for heavy usage | Pay per token; easy to start |
| Maintenance | You manage upgrades and scaling | Provider manages |
| Fine-tuning | Possible | Limited or provider-specific |

### Typical dimension sizes

| Dimensions | Example use |
|------------|-------------|
| 256-384 | Small/fast models, edge, low-cost large-scale search |
| 768-1024 | Strong general-purpose open models |
| 1536-3072+ | Large API/LLM-based models |

More dimensions generally capture more nuance but cost more storage and compute, with **diminishing returns**. If the model supports Matryoshka truncation, try 256/512/1024 on your eval set before committing.

### Fine-tuning embeddings

Consider fine-tuning when your domain vocabulary is specialized and off-the-shelf models underperform. You need (query, relevant document) pairs, ideally with hard negatives. Even a few thousand good pairs can help noticeably. Try cheaper wins first: better chunking, hybrid search, reranking, query rewriting.

---

## 16. Production Considerations

### 16.1 Never mix embedding models

Vectors from different models (or even different versions of the same model) live in **different spaces** and are **not comparable**. If you change models:
- **Re-embed everything** and build a new index.
- Store `model_name` and `model_version` with each vector.
- Use blue/green indexes: build the new index in parallel, evaluate, then switch traffic.

### 16.2 Incremental updates

- Track a **content hash** per chunk; re-embed only changed chunks.
- Handle deletions (remove stale vectors, or you'll retrieve outdated content).
- For HNSW, heavy deletes can degrade the graph; schedule periodic rebuilds/vacuum.
- For IVF/PQ, retrain centroids if the data distribution shifts substantially.

### 16.3 Latency budget (typical query)

| Step | Typical order of magnitude |
|------|---------------------------|
| Query embedding (API or local) | 10-200 ms |
| ANN search | 1-50 ms |
| Reranking (top 50) | 50-500 ms |
| LLM generation | 500 ms - several seconds |

Cache frequent queries and their embeddings.

### 16.4 Cost and scale levers

- Batch embedding calls; use async queues for ingestion.
- Deduplicate near-identical chunks.
- Use Matryoshka truncation or quantization (int8/binary) with full-precision rescoring.
- Choose HNSW for latency, IVF-PQ/DiskANN for memory/cost.

### 16.5 Security and privacy

- **Enforce access control at retrieval time** (metadata filters on tenant/user/role). Never rely on the LLM to hide content it was handed.
- Embeddings can **leak information**: research shows text can sometimes be partially reconstructed from embeddings ("embedding inversion"). Treat vector stores as sensitive as the source data.
- Beware **prompt injection** via retrieved documents (malicious text in a document instructing the LLM to misbehave). Sanitize/limit and keep system instructions authoritative.
- PII handling: redact or encrypt where required; consider data residency for hosted APIs.

### 16.6 Observability

Log: queries, retrieved chunk IDs and scores, latency per stage, user feedback (thumbs up/down), and "no good result" cases. These logs become your next evaluation set.

### 16.7 Multilingual notes

- Use a multilingual model if queries and documents span languages (e.g., English + Hindi); these map different languages to a shared space for cross-lingual retrieval.
- Mixed-script text (e.g., romanized Hindi/"Hinglish") is harder; test explicitly.
- Tokenizers vary in efficiency per language, so token limits may cover fewer words in some scripts.

---

## 17. Common Pitfalls and Best Practices

### Pitfalls

1. **Truncation without noticing.** Text over the model's limit is silently cut. Check token counts.
2. **Wrong or missing prefixes** (`query:` / `passage:` etc.). Read the model card.
3. **Mismatched metrics.** Index configured for L2 while model expects cosine/dot.
4. **Forgetting normalization** when using dot-product indexes.
5. **Mixing models/versions** in one index.
6. **Chunks without context** ("It increased by 5%." - what did?). Add titles/section paths.
7. **Ignoring parsing quality.** Broken PDF text makes broken embeddings.
8. **Relying on vector search only.** IDs, names, and codes need keyword/hybrid.
9. **Setting similarity thresholds from intuition.** Calibrate on your data.
10. **No evaluation set.** You can't improve what you can't measure.
11. **Retrieving too many chunks.** More context ≠ better answers; noise hurts LLMs.
12. **Ignoring freshness and deletes.** Stale vectors produce stale answers.
13. **Treating similarity as truth.** "Semantically similar" can still be factually irrelevant or contradictory (negation, e.g., "refunds are allowed" vs "refunds are not allowed" often embed very close).

### Best-practice checklist

- [ ] Start with a strong open or API embedding model and a **recursive/structure-aware chunker**
- [ ] Add **metadata** (title, section, source, date, permissions) to every chunk
- [ ] Use **hybrid search (BM25 + dense) with RRF**
- [ ] Add a **cross-encoder reranker** on the top 50-100
- [ ] Build a **retrieval eval set** early; track recall@k, MRR, nDCG
- [ ] Tune chunk size/overlap, `k`, and ANN parameters **empirically**
- [ ] Store **model name/version**; plan for re-embedding
- [ ] Enforce **access control in the retrieval layer**
- [ ] Monitor logs and feedback; feed failures back into the eval set
- [ ] Optimize cost last (quantization, dimension truncation) and **re-measure quality** after each change

---

## 18. FAQ

**Q: What exactly is the "meaning" in a vector? Can I read the dimensions?**
A: Individual dimensions are not human-interpretable. Meaning is encoded in the overall pattern and in the *relationships* between vectors (distances and directions).

**Q: How many dimensions do I need?**
A: Whatever your chosen model outputs (it's fixed by the model, unless Matryoshka truncation is supported). Typical: 384-3072.

**Q: Can I embed an entire document as a single vector?**
A: For short documents, yes. For long ones, a single vector blurs many topics together, and you may exceed the token limit. Chunk instead, or use a long-context model plus chunk-level pooling (late chunking).

**Q: Do I need a GPU?**
A: Not for small models and moderate volumes (CPU works). For big ingestion jobs or large models, a GPU speeds things up dramatically. Hosted APIs avoid the need entirely.

**Q: Why are my search results weird?**
A: Check, in order: chunking and parsing quality → model prefixes/normalization → metric mismatch → truncation → whether keyword/hybrid is needed → reranking.

**Q: Is semantic search better than keyword search?**
A: Neither universally. Semantic wins on meaning and paraphrase; keyword wins on exact terms and identifiers. **Hybrid is usually best.**

**Q: Can embeddings handle negation and numbers well?**
A: Only weakly. "Not covered by insurance" and "covered by insurance" can appear close. Numbers and exact values are poorly captured. Use rerankers, keyword filters, and structured data fields for such needs.

**Q: How often should I re-embed?**
A: When content changes (per chunk) or when you switch models. Not on a fixed schedule otherwise.

**Q: Embeddings vs fine-tuning an LLM for knowledge?**
A: Embeddings + RAG are better for factual, changing, citeable knowledge. Fine-tuning is better for style, format, and behavior.

**Q: What's the difference between an embedding and a hash?**
A: A hash maps similar inputs to *unrelated* outputs (change one character → totally different hash). An embedding maps *similar meanings* to *nearby* vectors.

---

## 19. Glossary

| Term | Meaning |
|------|---------|
| **Embedding / vector** | A list of numbers representing the meaning of a piece of data |
| **Dense vector** | Mostly non-zero values; fixed size (e.g., 768) |
| **Sparse vector** | Mostly zeros; one dimension per vocabulary term (e.g., TF-IDF, BM25, SPLADE) |
| **Token** | A word piece the model reads; the unit for length limits |
| **Transformer** | Neural network architecture built on self-attention |
| **Self-attention** | Mechanism letting each token weigh all other tokens for context |
| **Pooling** | Combining token vectors into one vector (mean, CLS, last-token) |
| **Bi-encoder** | Encodes query and document separately; enables precomputation |
| **Cross-encoder** | Scores a query-document pair jointly; used for reranking |
| **Contrastive learning** | Training that pulls related pairs together and pushes others apart |
| **Hard negative** | A confusing, non-relevant example that looks relevant |
| **Cosine similarity** | Angle-based similarity between vectors |
| **L2 normalization** | Scaling a vector to length 1 |
| **k-NN** | Find the k nearest vectors |
| **ANN** | Approximate nearest neighbor search, faster but slightly inexact |
| **HNSW** | Graph-based ANN index with hierarchical layers |
| **IVF** | Cluster-based ANN index (inverted file) |
| **PQ** | Product quantization; lossy vector compression |
| **Recall@k** | Fraction of relevant items found in the top k |
| **Chunk** | A segment of a document that gets its own embedding |
| **RAG** | Retrieval-Augmented Generation: retrieve context, then generate with an LLM |
| **BM25** | Classic keyword ranking function |
| **RRF** | Reciprocal Rank Fusion; merges multiple ranked lists |
| **Reranker** | Model that reorders a shortlist by finer relevance scoring |
| **HyDE** | Embed an LLM-written hypothetical answer to improve retrieval |
| **Matryoshka embeddings** | Vectors whose prefixes are valid lower-dimensional embeddings |
| **MTEB** | Benchmark suite for embedding models |
| **ColBERT** | Multi-vector, late-interaction retrieval approach |

---

## 20. Further Reading

**Foundational papers**
- *Efficient Estimation of Word Representations in Vector Space* (Word2Vec), Mikolov et al., 2013
- *GloVe: Global Vectors for Word Representation*, Pennington et al., 2014
- *Attention Is All You Need*, Vaswani et al., 2017
- *BERT: Pre-training of Deep Bidirectional Transformers*, Devlin et al., 2018
- *Sentence-BERT*, Reimers & Gurevych, 2019
- *Dense Passage Retrieval for Open-Domain QA* (DPR), Karpukhin et al., 2020
- *ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction*, Khattab & Zaharia, 2020
- *Efficient and Robust ANN Search Using HNSW Graphs*, Malkov & Yashunin, 2016/2018
- *Product Quantization for Nearest Neighbor Search*, Jégou et al., 2011
- *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, Lewis et al., 2020
- *MTEB: Massive Text Embedding Benchmark*, Muennighoff et al., 2022
- *Matryoshka Representation Learning*, Kusupati et al., 2022
- *Precise Zero-Shot Dense Retrieval without Relevance Labels* (HyDE), Gao et al., 2022

**Tools and documentation**
- Sentence-Transformers documentation (sbert.net)
- FAISS wiki (github.com/facebookresearch/faiss)
- pgvector (github.com/pgvector/pgvector)
- MTEB leaderboard on Hugging Face
- Documentation of your chosen vector database (Qdrant, Weaviate, Milvus, Pinecone, Chroma)

---

### One-Paragraph Summary

> A **document embedding** is a list of numbers produced by a neural network (usually a Transformer) that was trained with contrastive learning so that texts with similar meaning get nearby vectors. To build a search system, you **clean and chunk** your documents, **embed** each chunk, and **store** the vectors in an **ANN index** (such as HNSW). At query time you embed the question with the same model, find the **nearest chunk vectors** by cosine similarity, optionally combine with **keyword search** and a **reranker**, and either show the results or feed them to an LLM (**RAG**). Quality depends most on **parsing, chunking, model choice, hybrid retrieval, and measuring results on your own evaluation set**.
