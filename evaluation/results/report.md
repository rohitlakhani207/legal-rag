# Evaluation report — `20261006T062837Z`

| Approach | Retrieval Recall@5 | Citation Accuracy | Faithfulness | Avg. Latency |
|---|---:|---:|---:|---:|
| Vector | 90.0% | 80.0% | **75.8%** | 59.7 s |
| Hybrid | 90.0% | 80.0% | 74.5% | **59.4 s** |
| Hybrid + Reranker | **98.6%** | **94.3%** | 72.2% | 60.6 s |

<sub>40 questions (35 answerable, 5 unanswerable) · generator `qwen3.5:4b` · judge `qwen3.5:4b` · embeddings `BAAI/bge-base-en-v1.5` · reranker `Xenova/ms-marco-MiniLM-L-12-v2` · CPU only (8 cores, 14.3 GB RAM) · run `20261006T062837Z`</sub>

## All metrics

| Metric | Vector | Hybrid | Hybrid + Reranker |
|---|---:|---:|---:|
| Retrieval recall@k | 90.0% | 90.0% | 98.6% |
| Hit rate (≥1 gold provision retrieved) | 94.3% | 94.3% | 100.0% |
| MRR | 0.869 | 0.813 | 0.913 |
| Citation accuracy | 80.0% | 80.0% | 94.3% |
| Citation precision | 66.0% | 62.1% | 62.1% |
| Faithfulness | 75.8% | 74.5% | 72.2% |
| Abstained on answerable questions | 8.6% | 11.4% | 2.9% |
| Abstained on unanswerable questions (higher is better) | 100.0% | 100.0% | 100.0% |
| Avg. end-to-end latency | 59.7 s | 59.4 s | 60.6 s |
| p95 end-to-end latency | 74.3 s | 78.0 s | 74.5 s |
| Avg. retrieval latency | 53 ms | 52 ms | 3,410 ms |
| Avg. generation latency | 59.7 s | 59.3 s | 57.2 s |

## Retrieval recall by question type

| Type | n | Vector | Hybrid | Hybrid + Reranker |
|---|---:|---:|---:|---:|
| cross-document | 3 | 50.0% | 50.0% | 83.3% |
| keyword | 12 | 100.0% | 100.0% | 100.0% |
| paraphrase | 12 | 91.7% | 83.3% | 100.0% |
| specific | 8 | 87.5% | 100.0% | 100.0% |

## Per-question results

| Question | Mode | Recall | Citation | Faithful | Latency | Retrieved |
|---|---|---:|---:|---:|---:|---|
| `gdpr-01` Within how many hours must a controller notify the supervisory authority of a personal data breach? | Vector | 100.0% | 100.0% | 66.7% | 49.2 s | GDPR Article 33, GDPR Article 34, GDPR Article 12 |
| `gdpr-02` When does a company have to tell the affected people themselves that their data was leaked? | Vector | 100.0% | 100.0% | 80.0% | 51.9 s | GDPR Article 33, GDPR Article 34, GDPR Article 14 |
| `gdpr-03` On what grounds can I demand that a company deletes everything it holds about me? | Vector | 100.0% | 100.0% | 40.0% | 73.6 s | GDPR Article 17, DPDP Act Section 8, GDPR Article 49, DPDP Act Section 12 |
| `gdpr-04` What is the maximum administrative fine for infringing the basic principles for processing, including conditions for consent? | Vector | 100.0% | 100.0% | 100.0% | 54.0 s | GDPR Article 83 |
| `gdpr-05` What are the lawful bases for processing personal data under the GDPR? | Vector | 100.0% | 100.0% | 75.0% | 56.4 s | GDPR Article 6, GDPR Article 10, GDPR Article 5 |
| `gdpr-06` What must a data protection impact assessment contain at a minimum? | Vector | 100.0% | 100.0% | 50.0% | 63.7 s | GDPR Article 35, GDPR Article 36 |
| `gdpr-07` In which situations is an organisation obliged to appoint a data protection officer? | Vector | 100.0% | 0.0% | 60.0% | 51.0 s | GDPR Article 38, GDPR Article 39, GDPR Article 37 |
| `gdpr-08` From what age can a child consent on their own to information society services under the GDPR? | Vector | 100.0% | 100.0% | 100.0% | 43.8 s | GDPR Article 8, GDPR Article 12, DPDP Act Section 9, GDPR Article 57 |
| `gdpr-09` Which categories of personal data are treated as special categories whose processing is prohibited by default? | Vector | 100.0% | 100.0% | 50.0% | 61.2 s | GDPR Article 9, GDPR Article 25 |
| `gdpr-10` Can a bank reject my loan application purely through an algorithm without any human involvement? | Vector | 100.0% | 100.0% | 40.0% | 73.4 s | DPDP Act Section 17, GDPR Article 22, DPDP Act Section 6, GDPR Article 2 |
| `gdpr-11` Can I get my data from one online service in a machine-readable format and move it to a competitor? | Vector | 100.0% | 100.0% | 60.0% | 65.2 s | GDPR Article 20, GDPR Article 45, GDPR Article 49, GDPR Article 15, DPDP Act Section 17 |
| `gdpr-12` How long does a controller have to respond to a data subject's request, and can that period be extended? | Vector | 100.0% | 100.0% | 100.0% | 61.2 s | GDPR Article 12, GDPR Article 42, GDPR Article 33, GDPR Article 36, GDPR Article 13 |
| `gdpr-13` What must a contract between a controller and a processor stipulate? | Vector | 100.0% | 0.0% | 50.0% | 61.3 s | GDPR Article 28, GDPR Article 29, GDPR Article 31 |
| `gdpr-14` Are small companies with fewer than 250 employees exempt from keeping records of processing activities? | Vector | 100.0% | 100.0% | 75.0% | 58.3 s | GDPR Article 30, GDPR Article 88, GDPR Article 27 |
| `gdpr-15` Under what condition can personal data be sent to a non-EU country without any specific authorisation? | Vector | 100.0% | 100.0% | 75.0% | 69.0 s | GDPR Article 45, GDPR Article 49, GDPR Article 48, GDPR Article 46, GDPR Article 44 |
| `gdpr-16` What does data protection by design and by default require from controllers? | Vector | 100.0% | 100.0% | 50.0% | 61.2 s | GDPR Article 25, GDPR Article 14, GDPR Article 13, GDPR Article 70 |
| `gdpr-17` What are the principles relating to processing of personal data, such as purpose limitation and storage limitation? | Vector | 100.0% | 100.0% | 75.0% | 59.1 s | GDPR Article 5, GDPR Article 6, GDPR Article 9 |
| `gdpr-18` Does the GDPR apply to a US company with no EU office that tracks the online behaviour of people in Europe? | Vector | 0.0% | 0.0% | 100.0% | 52.8 s | GDPR Article 27, GDPR Article 40, GDPR Article 48, GDPR Article 96 |
| `gdpr-19` Which technical measures, such as encryption, does the GDPR list for ensuring the security of processing? | Vector | 100.0% | 100.0% | 83.3% | 67.5 s | GDPR Article 32, GDPR Article 6, GDPR Article 9, GDPR Article 30, GDPR Article 24 |
| `gdpr-20` If a company's mishandling of my personal data caused me financial or emotional harm, can I get compensation? | Vector | 100.0% | 0.0% | 80.0% | 54.7 s | GDPR Article 82, GDPR Article 33, GDPR Article 34 |
| `dpdp-01` Under India's DPDP Act, what must a Data Fiduciary do when a personal data breach occurs? | Vector | 100.0% | 100.0% | 75.0% | 72.2 s | DPDP Act Section 8, DPDP Act Section 10, DPDP Act Section 11 |
| `dpdp-02` What is the maximum penalty under the DPDP Act for failing to take reasonable security safeguards to prevent a personal data breach? | Vector | 100.0% | 100.0% | 100.0% | 61.1 s | DPDP Act Schedule, DPDP Act Section 33, DPDP Act Section 8, DPDP Act Section 27 |
| `dpdp-03` Up to what age is a person treated as a child under the Digital Personal Data Protection Act, 2023? | Vector | 0.0% | 0.0% | 100.0% | 46.6 s | DPDP Act Section 9, GDPR Article 8, GDPR Article 12, DPDP Act Section 1 |
| `dpdp-04` What does an Indian app need before it can process personal data of kids, and what is it forbidden from doing with that data? | Vector | 100.0% | 100.0% | 75.0% | 49.4 s | DPDP Act Section 9, DPDP Act Section 16, DPDP Act Section 17, DPDP Act Section 3 |
| `dpdp-05` What are the requirements for valid consent under the DPDP Act? | Vector | 100.0% | 100.0% | 75.0% | 68.8 s | DPDP Act Section 6, DPDP Act Section 4, DPDP Act Section 9 |
| `dpdp-06` What information must the notice to a Data Principal contain when consent is requested under the DPDP Act? | Vector | 100.0% | 100.0% | 83.3% | 76.9 s | DPDP Act Section 5, DPDP Act Section 6 |
| `dpdp-07` What obligations do individuals themselves have when exercising their data rights under Indian law, for example around false complaints? | Vector | 100.0% | 100.0% | 75.0% | 64.1 s | DPDP Act Section 15, DPDP Act Section 17, GDPR Article 77, GDPR Article 80, DPDP Act Section 8 |
| `dpdp-08` For which certain legitimate uses can a Data Fiduciary process personal data without consent under the DPDP Act? | Vector | 100.0% | 100.0% | 75.0% | 68.6 s | DPDP Act Section 7, DPDP Act Section 9, DPDP Act Section 11, DPDP Act Section 4, DPDP Act Section 8 |
| `dpdp-09` Can an Indian company send customer personal data to servers abroad? | Vector | 100.0% | 0.0% | 40.0% | 63.1 s | DPDP Act Section 16, GDPR Article 46, GDPR Article 44, GDPR Article 45, DPDP Act Section 17 |
| `dpdp-10` What additional obligations apply to a Significant Data Fiduciary? | Vector | 100.0% | 100.0% | 80.0% | 57.6 s | DPDP Act Section 10, DPDP Act Section 8 |
| `dpdp-11` Where and within how many days can a person appeal against an order of the Data Protection Board of India? | Vector | 100.0% | 0.0% | 75.0% | 52.2 s | DPDP Act Section 29, GDPR Article 66, DPDP Act Section 17 |
| `dpdp-12` Does the Indian data protection law cover personal information that someone has posted publicly on social media themselves? | Vector | 100.0% | 100.0% | 66.7% | 44.8 s | DPDP Act Section 3, DPDP Act Section 16, DPDP Act Section 7, GDPR Article 86, DPDP Act Section 11 |
| `cross-01` How do the GDPR and India's DPDP Act differ on the deadline for reporting a personal data breach to the regulator? | Vector | 50.0% | 100.0% | 40.0% | 74.3 s | DPDP Act Section 1, GDPR Article 33, DPDP Act Schedule, DPDP Act Section 3, DPDP Act Section 17 |
| `cross-02` Compare the age below which parental consent is needed for children's data under the GDPR and the DPDP Act. | Vector | 50.0% | 100.0% | 60.0% | 82.7 s | GDPR Article 8, DPDP Act Section 9, GDPR Article 12, DPDP Act Section 11 |
| `cross-03` What are the highest monetary penalties under the GDPR and under India's DPDP Act? | Vector | 50.0% | 100.0% | 100.0% | 71.2 s | DPDP Act Schedule, DPDP Act Section 33, DPDP Act Section 16, DPDP Act Section 10, DPDP Act Section 34 |
| `neg-01` What is the statute of limitations for a breach of contract claim in California? | Vector | — | — | 100.0% | 46.6 s | DPDP Act Section 8, DPDP Act Schedule, DPDP Act Section 33, GDPR Article 82 |
| `neg-02` What are the formal requirements for a valid will under English law? | Vector | — | — | 100.0% | 47.3 s | GDPR Article 46, GDPR Article 6, GDPR Article 47, GDPR Article 55 |
| `neg-03` What is the corporate income tax rate for domestic companies in India? | Vector | — | — | 100.0% | 43.1 s | DPDP Act Section 17, DPDP Act Section 16, DPDP Act Schedule, DPDP Act Section 34 |
| `neg-04` How many weeks of paid maternity leave are employees entitled to in the EU? | Vector | — | — | 100.0% | 49.9 s | GDPR Article 64, GDPR Article 88, GDPR Article 65, GDPR Article 62, GDPR Article 54 |
| `neg-05` What is the maximum prison sentence for copyright infringement under US federal law? | Vector | — | — | 100.0% | 59.3 s | GDPR Article 83, DPDP Act Schedule, DPDP Act Section 33 |
| `gdpr-01` Within how many hours must a controller notify the supervisory authority of a personal data breach? | Hybrid | 100.0% | 100.0% | 50.0% | 43.1 s | GDPR Article 33, GDPR Article 34, GDPR Article 12 |
| `gdpr-02` When does a company have to tell the affected people themselves that their data was leaked? | Hybrid | 100.0% | 100.0% | 50.0% | 60.1 s | GDPR Article 90, GDPR Article 34, GDPR Article 13, GDPR Article 15, GDPR Article 14 |
| `gdpr-03` On what grounds can I demand that a company deletes everything it holds about me? | Hybrid | 100.0% | 100.0% | 80.0% | 54.9 s | GDPR Article 17, DPDP Act Section 17, DPDP Act Section 4, GDPR Article 18, GDPR Article 21 |
| `gdpr-04` What is the maximum administrative fine for infringing the basic principles for processing, including conditions for consent? | Hybrid | 100.0% | 100.0% | 100.0% | 57.6 s | GDPR Article 83, GDPR Article 7 |
| `gdpr-05` What are the lawful bases for processing personal data under the GDPR? | Hybrid | 100.0% | 100.0% | 100.0% | 47.1 s | GDPR Article 10, GDPR Article 6, GDPR Article 21, GDPR Article 13, GDPR Article 14 |
| `gdpr-06` What must a data protection impact assessment contain at a minimum? | Hybrid | 100.0% | 0.0% | 66.7% | 63.6 s | GDPR Article 35, GDPR Article 36 |
| `gdpr-07` In which situations is an organisation obliged to appoint a data protection officer? | Hybrid | 100.0% | 0.0% | 66.7% | 61.3 s | GDPR Article 37, GDPR Article 38, GDPR Article 39 |
| `gdpr-08` From what age can a child consent on their own to information society services under the GDPR? | Hybrid | 100.0% | 100.0% | 100.0% | 42.4 s | GDPR Article 8, GDPR Article 7, DPDP Act Section 9, GDPR Article 21 |
| `gdpr-09` Which categories of personal data are treated as special categories whose processing is prohibited by default? | Hybrid | 100.0% | 100.0% | 25.0% | 48.4 s | GDPR Article 9, GDPR Article 25 |
| `gdpr-10` Can a bank reject my loan application purely through an algorithm without any human involvement? | Hybrid | 0.0% | 0.0% | 25.0% | 52.0 s | DPDP Act Section 17, GDPR Article 60, DPDP Act Section 5, GDPR Article 2 |
| `gdpr-11` Can I get my data from one online service in a machine-readable format and move it to a competitor? | Hybrid | 100.0% | 100.0% | 60.0% | 78.0 s | GDPR Article 20, DPDP Act Section 17, GDPR Article 12, DPDP Act Section 2, DPDP Act Section 8 |
| `gdpr-12` How long does a controller have to respond to a data subject's request, and can that period be extended? | Hybrid | 100.0% | 100.0% | 50.0% | 51.7 s | GDPR Article 12, GDPR Article 36, GDPR Article 13, GDPR Article 14 |
| `gdpr-13` What must a contract between a controller and a processor stipulate? | Hybrid | 100.0% | 0.0% | 100.0% | 57.0 s | GDPR Article 28, GDPR Article 6, GDPR Article 37 |
| `gdpr-14` Are small companies with fewer than 250 employees exempt from keeping records of processing activities? | Hybrid | 100.0% | 100.0% | 80.0% | 63.8 s | GDPR Article 30, DPDP Act Section 17 |
| `gdpr-15` Under what condition can personal data be sent to a non-EU country without any specific authorisation? | Hybrid | 100.0% | 100.0% | 80.0% | 56.4 s | GDPR Article 45, GDPR Article 46, GDPR Article 48, GDPR Article 49, GDPR Article 44 |
| `gdpr-16` What does data protection by design and by default require from controllers? | Hybrid | 100.0% | 100.0% | 75.0% | 43.4 s | GDPR Article 25, GDPR Article 37, GDPR Article 26 |
| `gdpr-17` What are the principles relating to processing of personal data, such as purpose limitation and storage limitation? | Hybrid | 100.0% | 100.0% | 100.0% | 58.1 s | GDPR Article 5, GDPR Article 6, GDPR Article 44, GDPR Article 9 |
| `gdpr-18` Does the GDPR apply to a US company with no EU office that tracks the online behaviour of people in Europe? | Hybrid | 100.0% | 100.0% | 60.0% | 65.1 s | GDPR Article 3, GDPR Article 27, GDPR Article 2, GDPR Article 22, GDPR Article 11 |
| `gdpr-19` Which technical measures, such as encryption, does the GDPR list for ensuring the security of processing? | Hybrid | 100.0% | 100.0% | 80.0% | 54.6 s | GDPR Article 32, GDPR Article 5, GDPR Article 30, GDPR Article 25 |
| `gdpr-20` If a company's mishandling of my personal data caused me financial or emotional harm, can I get compensation? | Hybrid | 100.0% | 100.0% | 40.0% | 65.9 s | GDPR Article 82, DPDP Act Section 8, DPDP Act Section 17, DPDP Act Section 2 |
| `dpdp-01` Under India's DPDP Act, what must a Data Fiduciary do when a personal data breach occurs? | Hybrid | 100.0% | 100.0% | 75.0% | 77.8 s | DPDP Act Section 10, DPDP Act Section 8, DPDP Act Schedule, DPDP Act Section 11 |
| `dpdp-02` What is the maximum penalty under the DPDP Act for failing to take reasonable security safeguards to prevent a personal data breach? | Hybrid | 100.0% | 100.0% | 75.0% | 62.0 s | DPDP Act Schedule, DPDP Act Section 33, DPDP Act Section 27, DPDP Act Section 8 |
| `dpdp-03` Up to what age is a person treated as a child under the Digital Personal Data Protection Act, 2023? | Hybrid | 100.0% | 0.0% | 100.0% | 47.4 s | GDPR Article 8, DPDP Act Section 9, DPDP Act Section 2, DPDP Act Section 3 |
| `dpdp-04` What does an Indian app need before it can process personal data of kids, and what is it forbidden from doing with that data? | Hybrid | 0.0% | 0.0% | 100.0% | 62.3 s | DPDP Act Section 4, DPDP Act Section 6, DPDP Act Section 7, GDPR Article 18 |
| `dpdp-05` What are the requirements for valid consent under the DPDP Act? | Hybrid | 100.0% | 100.0% | 80.0% | 67.5 s | DPDP Act Section 6 |
| `dpdp-06` What information must the notice to a Data Principal contain when consent is requested under the DPDP Act? | Hybrid | 100.0% | 100.0% | 33.3% | 99.9 s | DPDP Act Section 5, DPDP Act Section 6 |
| `dpdp-07` What obligations do individuals themselves have when exercising their data rights under Indian law, for example around false complaints? | Hybrid | 100.0% | 100.0% | 100.0% | 75.8 s | GDPR Article 77, DPDP Act Section 15, GDPR Article 80, DPDP Act Section 27, DPDP Act Section 6 |
| `dpdp-08` For which certain legitimate uses can a Data Fiduciary process personal data without consent under the DPDP Act? | Hybrid | 100.0% | 100.0% | 33.3% | 68.2 s | DPDP Act Section 7, DPDP Act Section 11, DPDP Act Section 8, DPDP Act Section 9 |
| `dpdp-09` Can an Indian company send customer personal data to servers abroad? | Hybrid | 100.0% | 100.0% | 75.0% | 62.6 s | DPDP Act Section 17, DPDP Act Section 7, DPDP Act Section 5, GDPR Article 88, DPDP Act Section 16 |
| `dpdp-10` What additional obligations apply to a Significant Data Fiduciary? | Hybrid | 100.0% | 0.0% | 83.3% | 68.1 s | DPDP Act Section 10, DPDP Act Section 8 |
| `dpdp-11` Where and within how many days can a person appeal against an order of the Data Protection Board of India? | Hybrid | 100.0% | 100.0% | 50.0% | 75.0 s | DPDP Act Section 29, DPDP Act Section 17, DPDP Act Section 16, GDPR Article 58 |
| `dpdp-12` Does the Indian data protection law cover personal information that someone has posted publicly on social media themselves? | Hybrid | 100.0% | 100.0% | 75.0% | 64.9 s | DPDP Act Section 3, GDPR Article 4, GDPR Article 9, DPDP Act Section 16 |
| `cross-01` How do the GDPR and India's DPDP Act differ on the deadline for reporting a personal data breach to the regulator? | Hybrid | 50.0% | 100.0% | 33.3% | 66.9 s | DPDP Act Schedule, GDPR Article 33, DPDP Act Section 27, DPDP Act Section 16 |
| `cross-02` Compare the age below which parental consent is needed for children's data under the GDPR and the DPDP Act. | Hybrid | 50.0% | 100.0% | 80.0% | 81.8 s | GDPR Article 8, DPDP Act Section 9, DPDP Act Section 6, GDPR Article 7 |
| `cross-03` What are the highest monetary penalties under the GDPR and under India's DPDP Act? | Hybrid | 50.0% | 100.0% | 100.0% | 43.4 s | DPDP Act Section 33, DPDP Act Schedule, DPDP Act Section 34, DPDP Act Section 16, DPDP Act Section 17 |
| `neg-01` What is the statute of limitations for a breach of contract claim in California? | Hybrid | — | — | 100.0% | 49.7 s | DPDP Act Schedule, DPDP Act Section 33, GDPR Article 33, DPDP Act Section 8 |
| `neg-02` What are the formal requirements for a valid will under English law? | Hybrid | — | — | 100.0% | 36.2 s | GDPR Article 40, GDPR Article 46, GDPR Article 66, GDPR Article 6 |
| `neg-03` What is the corporate income tax rate for domestic companies in India? | Hybrid | — | — | 100.0% | 43.5 s | DPDP Act Section 17, DPDP Act Section 16, DPDP Act Section 34 |
| `neg-04` How many weeks of paid maternity leave are employees entitled to in the EU? | Hybrid | — | — | 100.0% | 48.1 s | GDPR Article 64, GDPR Article 62, GDPR Article 82, GDPR Article 36, GDPR Article 65 |
| `neg-05` What is the maximum prison sentence for copyright infringement under US federal law? | Hybrid | — | — | 100.0% | 50.0 s | GDPR Article 83, GDPR Article 84, GDPR Article 77 |
| `gdpr-01` Within how many hours must a controller notify the supervisory authority of a personal data breach? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 55.2 s | GDPR Article 33, GDPR Article 36, GDPR Article 34, GDPR Article 14 |
| `gdpr-02` When does a company have to tell the affected people themselves that their data was leaked? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 74.5 s | GDPR Article 34, DPDP Act Section 8, GDPR Article 33, GDPR Article 22 |
| `gdpr-03` On what grounds can I demand that a company deletes everything it holds about me? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 56.2 s | GDPR Article 17, GDPR Article 21, DPDP Act Section 23, GDPR Article 28 |
| `gdpr-04` What is the maximum administrative fine for infringing the basic principles for processing, including conditions for consent? | Hybrid + Reranker | 100.0% | 100.0% | 66.7% | 55.4 s | GDPR Article 83, GDPR Article 7 |
| `gdpr-05` What are the lawful bases for processing personal data under the GDPR? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 57.7 s | GDPR Article 5, GDPR Article 10, GDPR Article 29, GDPR Article 6, GDPR Article 9 |
| `gdpr-06` What must a data protection impact assessment contain at a minimum? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 63.0 s | GDPR Article 35, GDPR Article 64 |
| `gdpr-07` In which situations is an organisation obliged to appoint a data protection officer? | Hybrid + Reranker | 100.0% | 100.0% | 40.0% | 66.6 s | GDPR Article 37, DPDP Act Section 10, GDPR Article 38, GDPR Article 39 |
| `gdpr-08` From what age can a child consent on their own to information society services under the GDPR? | Hybrid + Reranker | 100.0% | 100.0% | 100.0% | 48.5 s | GDPR Article 8, GDPR Article 21, GDPR Article 12, GDPR Article 17, GDPR Article 4 |
| `gdpr-09` Which categories of personal data are treated as special categories whose processing is prohibited by default? | Hybrid + Reranker | 100.0% | 100.0% | 33.3% | 52.8 s | GDPR Article 9, GDPR Article 47 |
| `gdpr-10` Can a bank reject my loan application purely through an algorithm without any human involvement? | Hybrid + Reranker | 100.0% | 100.0% | 40.0% | 76.0 s | GDPR Article 22, DPDP Act Section 17, DPDP Act Section 6, GDPR Article 52, GDPR Article 2 |
| `gdpr-11` Can I get my data from one online service in a machine-readable format and move it to a competitor? | Hybrid + Reranker | 100.0% | 100.0% | 60.0% | 64.4 s | GDPR Article 20, GDPR Article 12, DPDP Act Section 5, DPDP Act Section 6, GDPR Article 15 |
| `gdpr-12` How long does a controller have to respond to a data subject's request, and can that period be extended? | Hybrid + Reranker | 100.0% | 100.0% | 50.0% | 56.1 s | GDPR Article 12, GDPR Article 36, GDPR Article 33, GDPR Article 42, GDPR Article 15 |
| `gdpr-13` What must a contract between a controller and a processor stipulate? | Hybrid + Reranker | 100.0% | 0.0% | 75.0% | 63.5 s | GDPR Article 28, GDPR Article 31, GDPR Article 82 |
| `gdpr-14` Are small companies with fewer than 250 employees exempt from keeping records of processing activities? | Hybrid + Reranker | 100.0% | 100.0% | 50.0% | 56.8 s | GDPR Article 30, DPDP Act Section 17, GDPR Article 88 |
| `gdpr-15` Under what condition can personal data be sent to a non-EU country without any specific authorisation? | Hybrid + Reranker | 100.0% | 100.0% | 80.0% | 60.2 s | GDPR Article 46, GDPR Article 45, GDPR Article 48, GDPR Article 44, GDPR Article 49 |
| `gdpr-16` What does data protection by design and by default require from controllers? | Hybrid + Reranker | 100.0% | 100.0% | 80.0% | 59.8 s | GDPR Article 25, GDPR Article 47, GDPR Article 37, GDPR Article 11 |
| `gdpr-17` What are the principles relating to processing of personal data, such as purpose limitation and storage limitation? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 66.6 s | GDPR Article 5, GDPR Article 47, GDPR Article 6, GDPR Article 18 |
| `gdpr-18` Does the GDPR apply to a US company with no EU office that tracks the online behaviour of people in Europe? | Hybrid + Reranker | 100.0% | 100.0% | 100.0% | 52.8 s | GDPR Article 3, GDPR Article 68, GDPR Article 96, GDPR Article 27, GDPR Article 2 |
| `gdpr-19` Which technical measures, such as encryption, does the GDPR list for ensuring the security of processing? | Hybrid + Reranker | 100.0% | 100.0% | 80.0% | 63.0 s | GDPR Article 32, GDPR Article 25, GDPR Article 5, GDPR Article 35 |
| `gdpr-20` If a company's mishandling of my personal data caused me financial or emotional harm, can I get compensation? | Hybrid + Reranker | 100.0% | 100.0% | 80.0% | 65.9 s | GDPR Article 82, GDPR Article 34, GDPR Article 33, DPDP Act Section 8 |
| `dpdp-01` Under India's DPDP Act, what must a Data Fiduciary do when a personal data breach occurs? | Hybrid + Reranker | 100.0% | 100.0% | 60.0% | 70.0 s | DPDP Act Section 8, DPDP Act Section 16, DPDP Act Section 10, DPDP Act Section 27 |
| `dpdp-02` What is the maximum penalty under the DPDP Act for failing to take reasonable security safeguards to prevent a personal data breach? | Hybrid + Reranker | 100.0% | 100.0% | 100.0% | 65.1 s | DPDP Act Schedule, DPDP Act Section 33, DPDP Act Section 27, DPDP Act Section 8 |
| `dpdp-03` Up to what age is a person treated as a child under the Digital Personal Data Protection Act, 2023? | Hybrid + Reranker | 100.0% | 100.0% | 50.0% | 48.0 s | GDPR Article 8, DPDP Act Section 1, DPDP Act Section 44, DPDP Act Section 9, DPDP Act Section 2 |
| `dpdp-04` What does an Indian app need before it can process personal data of kids, and what is it forbidden from doing with that data? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 54.6 s | DPDP Act Section 9, DPDP Act Section 6, DPDP Act Section 16, DPDP Act Section 17 |
| `dpdp-05` What are the requirements for valid consent under the DPDP Act? | Hybrid + Reranker | 100.0% | 100.0% | 80.0% | 59.9 s | DPDP Act Section 6, DPDP Act Section 12, DPDP Act Section 5 |
| `dpdp-06` What information must the notice to a Data Principal contain when consent is requested under the DPDP Act? | Hybrid + Reranker | 100.0% | 100.0% | 66.7% | 72.4 s | DPDP Act Section 5, DPDP Act Section 6, DPDP Act Section 11 |
| `dpdp-07` What obligations do individuals themselves have when exercising their data rights under Indian law, for example around false complaints? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 67.3 s | DPDP Act Section 15, GDPR Article 80, DPDP Act Section 6, DPDP Act Section 10, DPDP Act Section 8 |
| `dpdp-08` For which certain legitimate uses can a Data Fiduciary process personal data without consent under the DPDP Act? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 70.4 s | DPDP Act Section 7, DPDP Act Section 4, DPDP Act Section 9, DPDP Act Section 8 |
| `dpdp-09` Can an Indian company send customer personal data to servers abroad? | Hybrid + Reranker | 100.0% | 100.0% | 40.0% | 68.1 s | DPDP Act Section 16, DPDP Act Section 17, GDPR Article 15, DPDP Act Section 3, GDPR Article 46 |
| `dpdp-10` What additional obligations apply to a Significant Data Fiduciary? | Hybrid + Reranker | 100.0% | 100.0% | 75.0% | 66.4 s | DPDP Act Section 10, DPDP Act Schedule, DPDP Act Section 8 |
| `dpdp-11` Where and within how many days can a person appeal against an order of the Data Protection Board of India? | Hybrid + Reranker | 100.0% | 100.0% | 66.7% | 60.9 s | DPDP Act Section 29, DPDP Act Section 2, DPDP Act Section 6, GDPR Article 66 |
| `dpdp-12` Does the Indian data protection law cover personal information that someone has posted publicly on social media themselves? | Hybrid + Reranker | 100.0% | 100.0% | 66.7% | 49.7 s | DPDP Act Section 3, DPDP Act Section 16, GDPR Article 86, DPDP Act Section 17, DPDP Act Section 6 |
| `cross-01` How do the GDPR and India's DPDP Act differ on the deadline for reporting a personal data breach to the regulator? | Hybrid + Reranker | 50.0% | 100.0% | 100.0% | 48.6 s | DPDP Act Section 16, GDPR Article 33, DPDP Act Section 17, DPDP Act Section 3 |
| `cross-02` Compare the age below which parental consent is needed for children's data under the GDPR and the DPDP Act. | Hybrid + Reranker | 100.0% | 100.0% | 25.0% | 79.3 s | GDPR Article 8, DPDP Act Section 9, DPDP Act Section 2, DPDP Act Section 40 |
| `cross-03` What are the highest monetary penalties under the GDPR and under India's DPDP Act? | Hybrid + Reranker | 100.0% | 0.0% | 50.0% | 71.5 s | DPDP Act Section 34, DPDP Act Schedule, DPDP Act Section 37, DPDP Act Section 33, GDPR Article 83 |
| `neg-01` What is the statute of limitations for a breach of contract claim in California? | Hybrid + Reranker | — | — | 100.0% | 55.4 s | DPDP Act Section 27, DPDP Act Schedule, DPDP Act Section 33, GDPR Article 58, DPDP Act Section 17 |
| `neg-02` What are the formal requirements for a valid will under English law? | Hybrid + Reranker | — | — | 100.0% | 48.3 s | GDPR Article 53, GDPR Article 8, DPDP Act Section 6, GDPR Article 6, GDPR Article 47 |
| `neg-03` What is the corporate income tax rate for domestic companies in India? | Hybrid + Reranker | — | — | 100.0% | 47.6 s | DPDP Act Section 17, DPDP Act Section 34, DPDP Act Section 3, DPDP Act Section 18 |
| `neg-04` How many weeks of paid maternity leave are employees entitled to in the EU? | Hybrid + Reranker | — | — | 100.0% | 48.5 s | GDPR Article 99, GDPR Article 64, GDPR Article 65, GDPR Article 62, GDPR Article 36 |
| `neg-05` What is the maximum prison sentence for copyright infringement under US federal law? | Hybrid + Reranker | — | — | 100.0% | 56.1 s | GDPR Article 84, GDPR Article 83 |

## Configuration

```json
{
  "generator_model": "qwen3.5:4b",
  "judge_model": "qwen3.5:4b",
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "reranker_model": "Xenova/ms-marco-MiniLM-L-12-v2",
  "top_k": 5,
  "candidates_per_retriever": 50,
  "rerank_candidates": 30,
  "rrf_k": 60,
  "fts_max_df": 0.2,
  "chunk_max_words": 220,
  "chunk_overlap_words": 40,
  "n_questions": 40,
  "retrieval_only": false,
  "hardware": {
    "machine": "x86_64",
    "cpus": 8,
    "memory_gb": 14.3,
    "system": "Linux"
  }
}
```
