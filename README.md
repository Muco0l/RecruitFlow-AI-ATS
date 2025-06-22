# RecruitFlow-AI-ATS

# 🤖 Intelligent Recruitment Automation System

A full-stack, agentic AI system designed to automate the end-to-end recruitment pipeline — from job description parsing and resume extraction to intelligent candidate-job matching and automated interview coordination.

> 🚀 Built using **Llama-2**, **LangChain**, **Streamlit**, and **PostgreSQL** for fast, scalable, and interactive hiring automation.

---

## 📅 Timeline

**Dec 2024 – Jan 2025**

---

## 🧩 Tech Stack

- **Llama-2** via Ollama (on-prem deployment)
- **LangChain** for agentic orchestration and prompt optimization
- **Streamlit** for interactive UI
- **PostgreSQL** (or SQLite during prototyping) for persistent storage

---

## ⚙️ Key Features

### 📝 Resume Parsing & Job Description Extraction
- Extracts structured information from PDF resumes and job descriptions.
- Converts unstructured data into analyzable formats using LLM-powered tools.

### 🧠 Candidate–Job Matching Engine
- Custom algorithm scores candidate-job fit based on skill, experience, and semantic relevance.
- Achieves **~85% accuracy** in early-stage evaluation.

### ✉️ Automated Email Generation
- Auto-generates personalized interview invite emails.
- Supports bulk processing of candidates.

### 📊 Scalable and Efficient
- Capable of processing **800+ resumes/day**.
- Boosts screening throughput by **3×** and reduces manual workload by **70%**.

### 🧪 LLM Fine-tuning & Optimization
- Integrated **LangChain** with Llama-2 using custom prompt tuning.
- Reduced hallucination by **25%** and improved response consistency and relevance.

---

## 🖥️ Architecture Overview

```plaintext
Streamlit UI ──▶ LangChain Agent ──▶ Llama-2 (Ollama) ──▶ PostgreSQL
                       │                     │
           Resume Parser / JD Extractor     Matching Engine
```
![RecruitFlow-AI-ATS]{img.png}
