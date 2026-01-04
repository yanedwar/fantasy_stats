# NHL Fantasy Weekly Scoring Tool

## Overview
This is a tool that pulls weekly boxscore data from a public NHL API. It computes the weekly fantasy hockey scores for both skaters and goalies according a set of configurable rules. The rules for this specific fantasy league are recorded below. 

The goal is to help track player performance over a given week without requiring constantly checking the fantasy league scoreboard personally.

## Features
- Fetches NHL game data from the public NHL API
- Processes boxscores and play-by-play events
- Detects special situations such as:
  - Short-handed goals
  - Power-play goals
  - Hat tricks
- Aggregates player stats across multiple games
- Computes fantasy points using a customizable scoring system
- Outputs weekly leaderboards

## Data Source
All data is retrieved from the public NHL API: [api-web.nhle.com](api-web.nhle.com)
