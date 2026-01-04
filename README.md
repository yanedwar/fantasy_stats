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

## Fantasy Rules
Skaters:
- 6.0 points for every goal
- 4.0 points for every assist
- 0.9 points for every shot
- 2.0 points for every short handed goal
- 2.0 points for a hat trick
- 0.4 points for every hit
- 0.6 points for every block
- 2.0 points for plus/minus
- 0.6 points for every takeaway

Goalies:
- 20.0 points for every goal
- 4.0 points for every assist
- 2.0 points for every short handed goal
- 5.0 points for a win
- 2.0 points for an overtime loss
- 5.0 points for a shutout
- 0.6 points for every save
- -3.0 point for every goal against
- 3.0 points for a game with a total save percentage greater than or equal to 0.910%

## Data Source
All data is retrieved from the public NHL API: [api-web.nhle.com](api-web.nhle.com)
