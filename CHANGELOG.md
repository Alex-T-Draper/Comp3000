# CHANGELOG

A record of key project milestones mapped to their git commits.

---

## Planning & Setup

### #1 Project vision and scope definition
- [`6605bb1`](../../commit/6605bb1c) – Initial commit

### #2 Literature review
- [`6605bb1`](../../commit/6605bb1c) – Initial commit

### #3 Ethics approval
- [`6605bb1`](../../commit/6605bb1c) – Initial commit

### #4 Risk assessment and Gantt chart
- [`6605bb1`](../../commit/6605bb1c) – Initial commit

---

## Core Development

### #5 Angular project setup
- [`6605bb1`](../../commit/6605bb1c) – Initial commit
- [`95183f0`](../../commit/95183f08) – Moved NLP files over to new GitHub Repository; started Angular frontend
- [`93dfed3`](../../commit/93dfed3c) – Trying to setup frontend for Generate Summary
- [`f5af89b`](../../commit/f5af89ba) – Major Works: updated frontend page, AI summary display

### #6 FastAPI backend setup
- [`95183f0`](../../commit/95183f08) – Moved NLP files over to new GitHub Repository
- [`95d6d01`](../../commit/95d6d01a) – Moved NLP, Tobii etc into backend folder

### #7 SQLite database schema
- [`1f326ab`](../../commit/1f326ab3) – Added Welcome page and introduced SQLite database
- [`0a9b26e`](../../commit/0a9b26e8) – Moved add_scroll_column into database.py; now creates correct schema

---

## ToS Conditions

### #8 Condition 1 – Plain Text
- [`e3e0d12`](../../commit/e3e0d124) – Created files for user testing conditions (ToS-plain)

### #9 Condition 2 – Scroll-Gate
- [`e3e0d12`](../../commit/e3e0d124) – Created files for user testing conditions (scroll-gate)

### #10 Condition 3 – Formatted
- [`eed3386`](../../commit/eed3386b) – Fixed bugs and Added tos-formatted; bolds and highlights important text
- [`0e36765`](../../commit/0e36765b) – Updated ToS formatted; body text renders as `<p>` elements, numbered sections

### #11 Condition 4 – AI Summary Panel
- [`93dfed3`](../../commit/93dfed3c) – Trying to setup frontend for Generate Summary
- [`f5af89b`](../../commit/f5af89ba) – Major Works: frontend now displays AI summary panel

### #12 Condition 5 – AI Enhanced
- [`482ffc9`](../../commit/482ffc99) – Bug fixes and updates: new ToS documents, improved NLP service

### #13 Condition 6 – AI Hover
- [`37cbe8d`](../../commit/37cbe8d8) – Created tos-AI-hover; hovering over highlighted text shows AI tooltip

---

## Eye Tracking

### #14 Tobii EyeX integration
- [`da39fc9`](../../commit/da39fc96) – Added Tobii SDK Files
- [`84b6a70`](../../commit/84b6a706) – Tobii Eye Tracking now functional; SDK tracks eye movement

### #15 Scroll-adjusted coordinate system
- [`26f5873`](../../commit/26f58733) – Eye tracking now accommodates for scrolling; detects scroll position

---

## NLP Service

### #16 NLP clause detection
- [`95183f0`](../../commit/95183f08) – Moved NLP files over to new GitHub Repository
- [`482ffc9`](../../commit/482ffc99) – Bug fixes and updates: improved NLP service
- [`4b48e52`](../../commit/4b48e521) – Update nlp_service.py
- [`b0bcd9e`](../../commit/b0bcd9ec) – Update nlp_service.py

### #17 Risk scoring algorithm
- [`482ffc9`](../../commit/482ffc99) – Bug fixes and updates: improved NLP service
- [`4b48e52`](../../commit/4b48e521) – Update nlp_service.py
- [`b0bcd9e`](../../commit/b0bcd9ec) – Update nlp_service.py

### #18 DistilBART summarisation
- [`f5af89b`](../../commit/f5af89ba) – Major Works: AI summary generation working
- [`16efb2b`](../../commit/16efb2b1) – Just changed summarize path for consistency
- [`4b48e52`](../../commit/4b48e521) – Update nlp_service.py
- [`b0bcd9e`](../../commit/b0bcd9ec) – Update nlp_service.py

### #19 Model benchmarking
- [`484cbcc`](../../commit/484cbcc5) – Updated Test models; implemented GPU testing
- [`fb3e545`](../../commit/fb3e5459) – Added script for CPU versus GPU benchmarks

---

## Study Design

### #20 Comprehension test design
- [`f8138b2`](../../commit/f8138b2a) – Added Comprehension Test and AI Generated Distractor Games
- [`67d34da`](../../commit/67d34dab) – Updated Comprehension Tests and app.py; added more questions

### #21 Distractor tasks
- [`f8138b2`](../../commit/f8138b2a) – Added Comprehension Test and AI Generated Distractor Games
- [`a6a9dad`](../../commit/a6a9dadb) – Update distractor-reaction-time.html

### #22 Post-study questionnaire
- [`594910b`](../../commit/594910b2) – Added Thank you page; created Google Form exit questionnaire

---

## Quality Assurance

### #23 CI/CD pipeline
- [`872ee5b`](../../commit/872ee5b7) – Added workflows for CI/CD
- [`8ccd968`](../../commit/8ccd9686) – Updated workflow files
- [`7161052`](../../commit/7161052b) – Fixing Frontend CI/CD
- [`b11011a`](../../commit/b11011a7) – Trying to fix backend CI/CD error
- [`800bcf6`](../../commit/800bcf69) – Update frontend.yml
- [`69e0a16`](../../commit/69e0a169) – Fixing Frontend actions
- [`203c76b`](../../commit/203c76b5) – Updated test and workflows

### #24 Unit tests
- [`b4a54b2`](../../commit/b4a54b20) – Added services tests
- [`d986ca3`](../../commit/d986ca39) – Updated test files; created tests for eye-tracking, NLP, and tracking
- [`68c8d90`](../../commit/68c8d90b) – Frontend Component Tests Completed; tests for all frontend components
- [`cd271e8`](../../commit/cd271e82) – Created backend tests; NLP tests folder and test files
- [`203c76b`](../../commit/203c76b5) – Updated test and workflows

---

## Data Collection & Analysis

### #25 Pilot study (N=2)
- [`85a1dee`](../../commit/85a1dee7) – Gethin's Test Completed *(pilot participant)*
- [`e504186`](../../commit/e5041861) – Carmen Tests done *(pilot participant)*

### #26 Fixed-position Continue button
- [`064597b`](../../commit/064597b5) – Updated button layout; changed button label to "Continue"

### #27 Data collection (N=10)
- [`a5c2911`](../../commit/a5c29116) – Test Ready
- [`e504186`](../../commit/e5041861) – Carmen Tests done
- [`85a1dee`](../../commit/85a1dee7) – Gethin's Test Completed
- [`357ca36`](../../commit/357ca367) – Nikodem Completed Test
- [`a724756`](../../commit/a7247565) – Gabriel and Mo completed tests
- [`3737471`](../../commit/3737471c) – Jaey finished test
- [`e6ee265`](../../commit/e6ee2658) – Ben and Amy completed
- [`653ea93`](../../commit/653ea934) – Isla finished test
- [`1906e15`](../../commit/1906e154) – Jake test completed (all 10 participants done)

### #28 Dissertation writing
- [`a968ed0`](../../commit/a968ed0c) – Create dissertation figure scripts
- [`1906e15`](../../commit/1906e154) – All visualisation figures ready for dissertation

### #29 Data analysis
- [`b2243863`](../../commit/b2243863) – Create dissertation figure scripts; scripts generate figures from data
- [`a968ed0`](../../commit/a968ed0c) – Added more figure scripts; modified for dissertation data
- [`fb3e545`](../../commit/fb3e5459) – Added script for CPU versus GPU benchmarks
- [`1906e15`](../../commit/1906e154) – Added NLP visualization outputs; AOI, bubbles, and scan paths

---

## Release

### #30 Final release v1.0.0
- [`c30d87f`](../../commit/c30d87f5) – Ready for deployment

### #31 Viva preparation
- [`c30d87f`](../../commit/c30d87f5) – Ready for deployment
