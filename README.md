📊 MyPolls
An Independent, Transparent, AI-Driven Political Data Platform (Work in Progress)

MyPolls is a fully automated system for aggregating, calibrating, and modeling political polling data using machine learning and transparent statistical logic.

The project started from a simple but uncomfortable reality:

In many countries, political polls are often used less to inform the public and more to shape narratives — amplifying fear, manufacturing momentum, or serving as propaganda tools for political actors.

MyPolls exists to challenge that model.

Instead of treating polls as headlines, MyPolls treats them as raw data that must be evaluated, corrected, and weighted based on measurable historical accuracy.

🚧 Project Status

MyPolls is an active work in progress.
Core systems are functional, but new features, improvements, and refinements are continuously being developed.

Planned and ongoing work includes:
expanding historical datasets
improving ML calibration and evaluation
enriching country-level dashboards
adding deeper visual analytics and transparency tools

🎯 Core Principles

No political alignment — the system does not promote candidates or ideologies

Transparency over hype — every adjustment is explainable and data-driven

Accuracy matters — polling institutions are evaluated based on past performance

Automation first — minimal manual intervention, reproducible results

🧠 What MyPolls Does
🔄 Fully Automated Data Pipeline

Fetches official election results

Collects and merges the latest polling data

Cleans and normalizes inconsistent sources

Removes duplicates and invalid entries

📐 Statistical Aggregation Engine

Time-decay weighting (recent polls matter more)

Sample size weighting

Institute-level and candidate-level accuracy calibration

Error-based penalization

Aggregated margin of error calculation

🤖 Machine Learning Layer

Trains a RandomForest regression model

Each (poll × candidate) becomes a training sample

Predicts final election results based on:

institute

methodology

timing

raw poll percentages

historical accuracy

Aggregates ML predictions using weighted averages

📈 Continuous Self-Improvement

Historical prediction snapshots are stored

Polling institutes can be re-evaluated over time

The model can be retrained as new data appears

🌍 Interactive Frontend (In Progress)

European political map visualization

Country-level dashboards

Election and polling overviews

Designed for clarity, not sensationalism

🧪 Not a Forecast. Not a Poll. A Model.

MyPolls does not claim to predict the future with certainty.

It provides:

a calibrated estimate

based on historical performance

using transparent, auditable logic

No hype. No spin. Just data.

⚠️ Disclaimer

This project is experimental and educational.
It is not affiliated with any political party, institution, or media organization and should not be considered an official electoral forecast.
