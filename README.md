# **Fashion E-Commerce ML System**

### *Hybrid Recommender • NLP • Forecasting • Segmentation • Funnel Analytics*

This project implements a full end-to-end Machine Learning pipeline for a fashion e-commerce platform. It converts raw transactional, product, review, and behavioral data into meaningful insights, personalized recommendations, demand forecasts, and customer intelligence.

---

## **Repository Structure**

This repository contains the complete and final implementation of the project.

The intermediate development repository, containing earlier development stages, experimentation, and incremental project progress, can be found here:

🔗 **Intermediate Development Repository:**
https://github.com/Srijaali/ml-based_Fashion-Ecommerce

---

## **Features**

### **1. Hybrid Recommendation System**

* Collaborative Filtering (Implicit ALS / MF)
* Content-Based Similarity (TF-IDF + BERT embeddings)
* Final Hybrid Model: CF + Content + Popularity + Behavior Re-ranking

### **2. NLP Review Intelligence**

* BERT-based sentiment classification
* Sentence-Transformer embeddings
* Topic signals + toxicity detection
* Category-level sentiment trends

### **3. Time-Series Forecasting**

* Prophet / ARIMA for article & category demand
* Seasonality patterns, trend detection
* Inventory risk alerts

### **4. Customer Segmentation**

* Clustering (K-Means / GMM / HDBSCAN)
* RFM scores, behavior ratios, category preferences
* Segment-based personalization

### **5. Funnel Analytics & Behavioral Insights**

* View → Click → Cart → Purchase paths
* Drop-off analysis
* Conversion KPIs + session trajectories

### **6. Trend & BI Insights**

* Trending vs declining products
* Price elasticity
* Customer lifecycle metrics
* Sales & category evolution

---

## **Project Pipeline**

```
1. Raw Data
2. Filtering & Cleaning
3. ETL → ML Datasets (A–F)
4. Preprocessing & Feature Engineering
5. EDA
6. Model Training (CF, CB, Hybrid, NLP, TS, Segmentation)
7. Hyperparameter Tuning
8. Final Models & Evaluations
9. Trend/BI Dashboards
10. API Serving & Integration
```

---

## **ML Datasets**

* **Dataset A:** User–Item interactions (CF)
* **Dataset B:** Article content features
* **Dataset C:** Customer features (RFM + behavior)
* **Dataset D:** Time-series sales
* **Dataset E:** Reviews (sentiment + embeddings)
* **Dataset F:** Behavioral events + funnels

These datasets drive all downstream ML models.

---

## **Tech Stack**

**Languages & Frameworks:**
Python, Pandas, scikit-learn, PyTorch, Sentence-BERT, Implicit, Prophet/ARIMA

**Storage & Processing:**
PostgreSQL, Parquet, NumPy

**Experimentation:**
MLflow

**Optional Serving:**
FastAPI, Docker

---

## **Results Delivered**

* High-quality hybrid recommender
* Robust sentiment-aware product intelligence
* Accurate demand forecasts
* Actionable customer segments
* Complete behavioral funnel metrics
* Comprehensive BI and trend insights

---

### Project Contributors  

<div align="center">
  <a href="https://www.linkedin.com/in/rayyanmerchant2004/" target="_blank">
    <img src="https://img.shields.io/badge/Rayyan%20Merchant-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white" alt="Rayyan Merchant"/>
  </a>
  <a href="https://www.linkedin.com/in/rija-ali-731095296" target="_blank">
    <img src="https://img.shields.io/badge/Syeda%20Rija%20Ali-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white" alt="Syeda Rija Ali"/>
  </a>
  <a href="https://www.linkedin.com/in/riya-bhart-339036287/" target="_blank">
    <img src="https://img.shields.io/badge/Riya%20Bhart-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white" alt="Riya Bhart"/>
  </a>
    <a href="https://www.linkedin.com/in/syed-ukkashah-28b334214/" target="_blank">
    <img src="https://img.shields.io/badge/Syed%20Ukkashah%20Ahmed-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white" alt="Syed Ukkashah Ahmed"/>
  </a>
</div>
