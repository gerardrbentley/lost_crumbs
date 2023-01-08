---
title: LightGBM Predicting Water Pump Functionality
description: DrivenData competition for fun Data Mining Tanzania Water Table data.
categories:
  - libraries
tags:
  - streamlit
  - python
  - intermediate
  - drivendata
links:
  - Prerequisites:
    - setups/python.md
date: 2022-04-19
---

# LightGBM Predicting Water Pump Functionality



Water Pump functionality prediction. Based on the DrivenData challenge [Pump it Up: Data Mining the Water Table](https://www.drivendata.org/competitions/7/pump-it-up-data-mining-the-water-table/page/23/)

See the exploration in [Streamlit Cloud](https://share.streamlit.io/gerardrbentley/pump-it-up/main) 🎈

For better performance, grab the code from [github repo](https://github.com/gerardrbentley/pump-it-up)

<blockquote class="twitter-tweet" data-theme="dark"><p lang="en" dir="ltr">Trying out LightGBM for a <a href="https://twitter.com/drivendataorg?ref_src=twsrc%5Etfw">@drivendataorg</a> competition assessing water pump functionality. Still need to work on the pre-processing before I go posting any scores though 😆<br><br>🕹 <a href="https://twitter.com/streamlit?ref_src=twsrc%5Etfw">@streamlit</a> Demo: <a href="https://t.co/P4XzP1t9vC">https://t.co/P4XzP1t9vC</a><br>🐙 Github Repo: <a href="https://t.co/nn1Ose9tL4">https://t.co/nn1Ose9tL4</a><a href="https://twitter.com/hashtag/30DaysOfStreamlit?src=hash&amp;ref_src=twsrc%5Etfw">#30DaysOfStreamlit</a></p>&mdash; @gar@gerardbentley.com (@GarsBar35Plus) <a href="https://twitter.com/GarsBar35Plus/status/1516588954346160131?ref_src=twsrc%5Etfw">April 20, 2022</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

## Project Walkthrough

Using data from [Taarifa](http://taarifa.org/) and the [Tanzanian Ministry of Water](http://maji.go.tz/), can we predict which pumps are functional, which need some repairs, and which don't work at all?

Predict one of these three classes based on a number of variables about what kind of pump is operating, when it was installed, and how it is managed.

A smart understanding of which waterpoints will fail can improve maintenance operations and ensure that clean, potable water is available to communities across Tanzania.

### Data Sources

- Training and test data from drivendata, along with submission format
  - Details in [problem description](https://www.drivendata.org/competitions/7/pump-it-up-data-mining-the-water-table/page/25/#features_list)

![driven data downloads](/images/lightgbm_water_pumps/2022-04-15-20-02-15.png)

### Feature Exploration and Engineering

Much of this was guided by the DrivenData Competition forum, specifically this user's [EDA + Catboost example](https://towardsdatascience.com/pump-it-up-with-catboost-828bf9eaac68) (I haven't tried out all of his data processing steps... yet)

## Credits

This package was created with Cookiecutter and the `gerardrbentley/cookiecutter-streamlit` project template.

- Cookiecutter: [https://github.com/audreyr/cookiecutter](https://github.com/audreyr/cookiecutter)
- `gerardrbentley/cookiecutter-streamlit`: [https://github.com/gerardrbentley/cookiecutter-streamlit](https://github.com/gerardrbentley/cookiecutter-streamlit)

### DrivenData Platform

```
@misc{<https://doi.org/10.48550/arxiv.1606.07781>,
  doi = {10.48550/ARXIV.1606.07781},

  url = {<https://arxiv.org/abs/1606.07781>},

  author = {Bull, Peter and Slavitt, Isaac and Lipstein, Greg},

  keywords = {Human-Computer Interaction (cs.HC), Computers and Society (cs.CY), Social and Information Networks (cs.SI), Machine Learning (stat.ML), FOS: Computer and information sciences, FOS: Computer and information sciences},

  title = {Harnessing the Power of the Crowd to Increase Capacity for Data Science in the Social Sector},

  publisher = {arXiv},

  year = {2016},

  copyright = {Creative Commons Attribution 4.0 International}
}
```