# H-Net++: Hierarchical Dynamic Chunking for Tokenizer-Free Language   Modelling in Morphologically-Rich Languages

## 基本信息

- **arXiv ID**: 2508.05628v1
- **发布日期**: 2025-08-07
- **主要分类**: cs.CL
- **所有分类**: cs.CL, cs.AI
- **作者**: Mehrdad Zakershahrak, Samira Ghodratnama

## 链接

- **arXiv页面**: https://arxiv.org/abs/2508.05628v1
- **PDF下载**: https://arxiv.org/pdf/2508.05628v1.pdf

## 摘要

Byte-level language models eliminate fragile tokenizers but face computational challenges in morphologically-rich languages (MRLs), where words span many bytes. We propose H-NET++, a hierarchical dynamic-chunking model that learns linguistically-informed segmentation through end-to-end training. Key innovations include: (1) a lightweight Transformer context-mixer (1.9M parameters) for cross-chunk attention, (2) a two-level latent hyper-prior for document-level consistency, (3) specialized handling of orthographic artifacts (e.g. Persian ZWNJ), and (4) curriculum-based training with staged sequence lengths. On a 1.4B-token Persian corpus, H-NET++ achieves state-of-the-art results: 0.159 BPB reduction versus BPE-based GPT-2-fa (12% better compression), 5.4pp gain on ParsGLUE, 53% improved robustness to ZWNJ corruption, and 73.8% F1 on gold morphological boundaries. Our learned chunks align with Persian morphology without explicit supervision, demonstrating that hierarchical dynamic chunking provides an effective tokenizer-free solution for MRLs while maintaining computational efficiency.
