# 五位置数据集的引用补全（2026-11-13 核对）

结论：五条都能补，且都有可核对的来源。可直接用 paper/references-datasets.bib；
如果 main.tex 继续用 thebibliography，用下面的 \bibitem 版本。

## 1. 核对结果

| 位置 | 数据集 | 引用键 | 正式来源 | 核对状态 |
|---|---|---|---|---|
| User Request Inspection | AgentHarm | agentharm2025 | ICLR 2025；arXiv:2410.09024 | arXiv comments 明写 Accepted at ICLR 2025 |
| External Content Inspection | InjecAgent | injecagent2024 | Findings of ACL 2024, pp. 10471–10506；doi 10.18653/v1/2024.findings-acl.624 | ACL Anthology 官方条目 |
| Tool Call Inspection | TS-Bench (ToolSafe) | toolsafe2026 | Findings of ACL 2026, pp. 37125–37153；doi 10.18653/v1/2026.findings-acl.1850 | ACL Anthology 官方条目；论文明确构建 TS-Bench |
| Action Inspection | StepShield | stepshield2026 | arXiv:2601.22136；仓库称 NeurIPS 2026 benchmark | 仅 preprint；venue 未见官方确认，需在投稿前再核 |
| Response Inspection | WildGuardTest | wildguard2024 | NeurIPS 2024 Datasets & Benchmarks；arXiv:2406.18495 | arXiv comments 明写 NeurIPS 2024 Camera Ready |

注意：
- 原表拼写 StepSheild 应为 StepShield。
- StepShield 建议位置名改为 In-flight Action Inspection（Prefix Monitoring），理由见 position-mapping 文档。
- TS-Bench 应写成 TS-Bench (ToolSafe)，因为 TS-Bench 由 ToolSafe 论文提出并发布。

## 2. 表格直接替换

\begin{verbatim}
User Request Inspection & AgentHarm~\cite{agentharm2025} & request only; harmful/benign; request \\
External Content Inspection & InjecAgent~\cite{injecagent2024} & request + tool return; injection present; item \\
Tool Call Inspection & TS-Bench~\cite{toolsafe2026} & request + history + tools + candidate action; safe/unsafe; step \\
In-flight Action Inspection & StepShield~\cite{stepshield2026} & task + observed prefix; trajectory rogue; trajectory \\
Response Inspection & WildGuardTest~\cite{wildguard2024} & request + response; response harm; response \\
\end{verbatim}

## 3. 如果 main.tex 用 thebibliography（当前就是）

把下面五条粘到 \end{thebibliography} 之前；不需要 bibtex。

\begin{verbatim}
\bibitem{agentharm2025}
M. Andriushchenko, A. Souly, M. Dziemian, D. Duenas, M. Lin, J. Wang, D. Hendrycks, A. Zou, Z. Kolter, M. Fredrikson, E. Winsor, J. Wynne, Y. Gal, and X. Davies.
\newblock {AgentHarm}: A Benchmark for Measuring Harmfulness of {LLM} Agents.
\newblock In \emph{International Conference on Learning Representations (ICLR)}, 2025.
\newblock arXiv:2410.09024.

\bibitem{injecagent2024}
Q. Zhan, Z. Liang, Z. Ying, and D. Kang.
\newblock {InjecAgent}: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents.
\newblock In \emph{Findings of the Association for Computational Linguistics: ACL 2024}, pages 10471--10506, 2024.
\newblock doi:10.18653/v1/2024.findings-acl.624.

\bibitem{toolsafe2026}
Y. Mou, Z. Xue, L. Li, P. Liu, S. Zhang, W. Ye, and J. Shao.
\newblock {ToolSafe}: Enhancing Tool Invocation Safety of {LLM}-based Agents via Proactive Step-level Guardrail and Feedback.
\newblock In \emph{Findings of the Association for Computational Linguistics: ACL 2026}, pages 37125--37153, 2026.
\newblock doi:10.18653/v1/2026.findings-acl.1850.

\bibitem{stepshield2026}
G. Felicia, Z. Sasindran, J. He, M. Eniolade, H. Kumar, and M. H. Angati.
\newblock {StepShield}: When, Not Whether to Intervene on Rogue Agents.
\newblock arXiv:2601.22136, 2026.
\newblock Preprint; project repository describes it as a NeurIPS 2026 benchmark (verify camera-ready venue).

\bibitem{wildguard2024}
S. Han, K. Rao, A. Ettinger, L. Jiang, B. Y. Lin, N. Lambert, Y. Choi, and N. Dziri.
\newblock {WildGuard}: Open One-Stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of {LLMs}.
\newblock In \emph{Advances in Neural Information Processing Systems (NeurIPS), Datasets and Benchmarks Track}, 2024.
\newblock arXiv:2406.18495.
\end{verbatim}

## 4. 如果改用 BibTeX

main.tex 现在没有 \bibliography；切换步骤：

1. 删除 \begin{thebibliography}...\end{thebibliography}。
2. 在末尾加：
\begin{verbatim}
\bibliographystyle{plainnat}   % 或 ACL 模板的 acl_natbib
\bibliography{references-datasets}
\end{verbatim}
3. 编译顺序：pdflatex -> bibtex -> pdflatex -> pdflatex。
4. note 字段里用了 \url；导言区需有 \usepackage{url}（或 hyperref）。
5. 如果期刊/会议模板要求数据集单独引用，再加下面这类条目：
\begin{verbatim}
@misc{agentharm-data,
  author       = {{AI Safety Institute}},
  title        = {{AgentHarm} Dataset},
  howpublished = {\url{https://huggingface.co/datasets/ai-safety-institute/AgentHarm}},
  note         = {Revision e23b3fe60a0da9037314b88e5ee3a0c054970dad},
  year         = {2024}
}
\end{verbatim}

## 5. 投稿前还需核的两件事

1. **StepShield 的 venue**：arXiv comments 没有写会议；仓库自称 NeurIPS 2026 benchmark。
   如果 camera-ready 未上线，建议正文写“preprint, arXiv:2601.22136”，不要写 NeurIPS。
2. **AgentHarm 的 ICLR 2025 版本**：arXiv comments 确认接收，但正式 proceedings 页码未核；
   引用 ICLR 2025 + arXiv 号即可，不需要页码。

## 6. 文件

- [references-datasets.bib](../references-datasets.bib)：五条 BibTeX（含数据集 URL note）。
- 本文件：核对表 + 表格替换 + \bibitem 版本 + BibTeX 切换步骤。