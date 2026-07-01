#!/usr/bin/env python3
# program_dashboard_renderer.py
# Purpose: Generate a per-program HTML dashboard in the 62443 gold-standard
#          style (light theme, dark navy header) from runs/[slug]/latest.json.
#          Handles schema 1.1 (62443, customer-portal) and schema 2.0 (hds,
#          iso42001) transparently.
# Style:   PEP 8, type hints throughout
# Governed by: config/constitution.md + functions/program-dashboard-spec.md
# Quality gate: constitutional alignment (IV.1, IV.2, IV.4, IV.14)
#
# Usage:
#   python scripts/program_dashboard_renderer.py --program 62443
#   python scripts/program_dashboard_renderer.py --program hds --output public/hds/index.html
#
# Inputs:  runs/[slug]/latest.json
# Outputs: public/[slug]/index.html  (or path given via --output)
#
# Dependencies: Standard library only.
# Repo path: scripts/program_dashboard_renderer.py

"""62443-style light-theme per-program compliance dashboard renderer."""

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# CSS — extracted from runs/62443/dashboard.html (gold standard)
# ---------------------------------------------------------------------------

CSS = """\
    :root {
      --bg: #f1f5f9;
      --surface: #ffffff;
      --surface-2: #f8fafc;
      --border: #e2e8f0;
      --text: #0f172a;
      --text-muted: #64748b;
      --text-light: #94a3b8;
      --primary: #0891b2;
      --primary-light: #cffafe;
      --critical: #dc2626;
      --critical-light: #fee2e2;
      --high: #ea580c;
      --high-light: #ffedd5;
      --medium: #ca8a04;
      --medium-light: #fef9c3;
      --low: #16a34a;
      --low-light: #dcfce7;
      --evidenced: #0891b2;
      --evidenced-light: #cffafe;
      --impl: #7c3aed;
      --impl-light: #ede9fe;
      --gap: #dc2626;
      --gap-light: #fee2e2;
      --na: #94a3b8;
      --na-light: #f1f5f9;
      --yellow-badge: #f59e0b;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
      --shadow: 0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
      --shadow-lg: 0 10px 15px rgba(0,0,0,0.06), 0 4px 6px rgba(0,0,0,0.05);
      --radius: 10px;
      --radius-sm: 6px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter',
           system-ui, sans-serif; background: var(--bg); color: var(--text);
           font-size: 14px; line-height: 1.5; min-height: 100vh; }
    .header { background: #0c1a2e; color: #fff; padding: 0 32px;
              display: flex; align-items: center; justify-content: space-between;
              height: 64px; position: sticky; top: 0; z-index: 100;
              box-shadow: 0 2px 8px rgba(0,0,0,0.4); }
    .header-left { display: flex; align-items: center; gap: 16px; }
    .header-logo { width: 38px; height: 38px;
                   background: linear-gradient(135deg, #0891b2, #0e7490);
                   border-radius: 8px; display: flex; align-items: center;
                   justify-content: center; font-size: 13px; font-weight: 800;
                   color: #fff; flex-shrink: 0; letter-spacing: -0.5px; }
    .header-title { font-size: 15px; font-weight: 700; color: #f1f5f9; }
    .header-subtitle { font-size: 11px; color: #64748b; margin-top: 1px; }
    .header-right { display: flex; align-items: center; gap: 20px; }
    .health-badge { display: flex; align-items: center; gap: 6px; padding: 5px 12px;
                    border-radius: 20px; font-size: 11px; font-weight: 700;
                    letter-spacing: 0.5px; text-transform: uppercase; }
    .health-badge.yellow { background: #78350f; color: #fde68a; }
    .health-badge.red    { background: #7f1d1d; color: #fecaca; }
    .health-badge.green  { background: #14532d; color: #bbf7d0; }
    .health-badge.unknown{ background: #1e293b; color: #94a3b8; }
    .health-dot { width: 7px; height: 7px; border-radius: 50%;
                  background: currentColor; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
    .run-meta { text-align: right; }
    .run-meta .label { font-size: 10px; color: #475569; text-transform: uppercase;
                       letter-spacing: 0.5px; }
    .run-meta .value { font-size: 12px; color: #cbd5e1; font-weight: 500; }
    .main { padding: 28px 32px; max-width: 1440px; margin: 0 auto; }
    .staleness-notice { background: #fef9c3; border: 1px solid #fde047;
                        border-left: 4px solid #ca8a04; border-radius: var(--radius);
                        padding: 12px 20px; margin-bottom: 20px; font-size: 12px;
                        color: #78350f; }
    .escalation-banner { background: var(--critical-light); border: 1px solid #fca5a5;
                         border-left: 4px solid var(--critical); border-radius: var(--radius);
                         padding: 16px 20px; margin-bottom: 24px; }
    .escalation-banner h2 { font-size: 12px; font-weight: 800; color: var(--critical);
                            text-transform: uppercase; letter-spacing: 0.8px;
                            margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
    .escalation-grid { display: grid;
                       grid-template-columns: repeat(auto-fit, minmax(260px,1fr)); gap: 8px; }
    .escalation-item { background: #fff; border: 1px solid #fca5a5;
                       border-radius: var(--radius-sm); padding: 10px 14px;
                       display: flex; gap: 10px; align-items: flex-start; }
    .escalation-num { flex-shrink: 0; width: 22px; height: 22px;
                      background: var(--critical); color: #fff; border-radius: 50%;
                      display: flex; align-items: center; justify-content: center;
                      font-size: 11px; font-weight: 700; margin-top: 1px; }
    .escalation-text { font-size: 12px; color: #7f1d1d; line-height: 1.4; }
    .escalation-action { font-size: 11px; color: var(--critical); font-weight: 600;
                         margin-top: 4px; }
    .stats-row { display: grid; grid-template-columns: repeat(5,1fr); gap: 14px;
                 margin-bottom: 24px; }
    @media (max-width:1100px) { .stats-row { grid-template-columns: repeat(3,1fr); } }
    @media (max-width:700px)  { .stats-row { grid-template-columns: repeat(2,1fr); } }
    .stat-card { background: var(--surface); border: 1px solid var(--border);
                 border-radius: var(--radius); padding: 18px 20px;
                 box-shadow: var(--shadow-sm); }
    .stat-label { font-size: 10px; font-weight: 700; text-transform: uppercase;
                  letter-spacing: 0.6px; color: var(--text-muted); margin-bottom: 8px; }
    .stat-value { font-size: 34px; font-weight: 800; line-height: 1; margin-bottom: 4px; }
    .stat-sub { font-size: 11px; color: var(--text-muted); }
    .stat-card.critical .stat-value { color: var(--critical); }
    .stat-card.warning  .stat-value { color: var(--high); }
    .stat-card.info     .stat-value { color: var(--primary); }
    .stat-card.neutral  .stat-value { color: var(--text); }
    .stat-card.ok       .stat-value { color: var(--low); }
    .stat-bar { height: 3px; border-radius: 2px; margin-top: 10px;
                background: var(--border); overflow: hidden; }
    .stat-bar-fill { height: 100%; border-radius: 2px; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
               margin-bottom: 20px; }
    .col-2 { grid-column: span 2; }
    @media (max-width:1000px) { .grid-2 { grid-template-columns: 1fr; }
                                .col-2 { grid-column: span 1; } }
    .card { background: var(--surface); border: 1px solid var(--border);
            border-radius: var(--radius); box-shadow: var(--shadow-sm);
            overflow: hidden; }
    .card-header { padding: 13px 20px; border-bottom: 1px solid var(--border);
                   display: flex; align-items: center; justify-content: space-between;
                   background: var(--surface-2); }
    .card-title { font-size: 12px; font-weight: 700; color: var(--text);
                  display: flex; align-items: center; gap: 8px;
                  text-transform: uppercase; letter-spacing: 0.4px; }
    .card-badge { font-size: 10px; font-weight: 700; padding: 2px 8px;
                  border-radius: 10px; background: var(--primary-light);
                  color: var(--evidenced); }
    .card-badge.warn { background: var(--critical-light); color: var(--critical); }
    .card-body { padding: 20px; }
    .section-label { font-size: 11px; font-weight: 700; text-transform: uppercase;
                     letter-spacing: 0.8px; color: var(--text-muted);
                     margin: 24px 0 12px; display: flex; align-items: center; gap: 10px; }
    .section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }
    .coverage-bar-track { height: 10px; background: var(--border); border-radius: 5px;
                          overflow: hidden; display: flex; margin: 14px 0 8px; }
    .coverage-bar-seg { height: 100%; }
    .cov-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .cov-table th { font-size: 10px; font-weight: 700; text-transform: uppercase;
                    letter-spacing: 0.4px; color: var(--text-muted);
                    padding: 6px 10px; border-bottom: 2px solid var(--border);
                    text-align: left; }
    .cov-table td { padding: 8px 10px; border-bottom: 1px solid var(--border); }
    .cov-table tr:last-child td { border-bottom: none; }
    .cov-table tr.totals-row td { font-weight: 700; background: var(--surface-2);
                                   border-top: 2px solid var(--border); }
    .risk-chart-grid { display: grid; grid-template-columns: 130px 1fr;
                       gap: 20px; align-items: center; }
    .donut-wrap { position: relative; width: 130px; height: 130px; flex-shrink: 0; }
    .donut-wrap svg { transform: rotate(-90deg); }
    .donut-center { position: absolute; top: 50%; left: 50%;
                    transform: translate(-50%,-50%); text-align: center; }
    .donut-center .big { font-size: 30px; font-weight: 800; color: var(--text); }
    .donut-center .sm  { font-size: 10px; color: var(--text-muted); font-weight: 600;
                         text-transform: uppercase; }
    .risk-legend { display: flex; flex-direction: column; gap: 10px; }
    .risk-legend-item { display: flex; align-items: center; gap: 10px; }
    .risk-legend-dot { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
    .risk-legend-label { font-size: 12px; color: var(--text-muted); flex: 1; }
    .risk-legend-count { font-size: 15px; font-weight: 800; min-width: 20px;
                         text-align: right; }
    .risk-legend-bar-track { flex: 1; height: 4px; background: var(--border);
                              border-radius: 2px; overflow: hidden; }
    .risk-legend-bar { height: 100%; border-radius: 2px; }
    .risk-item { padding: 8px 12px; border-radius: var(--radius-sm); margin-top: 8px;
                 border: 1px solid; }
    .risk-item.critical { background: var(--critical-light); border-color: #fca5a5; }
    .risk-item.high     { background: var(--high-light); border-color: #fdba74; }
    .risk-item.medium   { background: var(--medium-light); border-color: #fde047; }
    .risk-item.low      { background: var(--low-light); border-color: #86efac; }
    .risk-item-id { font-size: 10px; font-weight: 700; font-family: monospace;
                    margin-bottom: 3px; }
    .risk-item-title { font-size: 12px; line-height: 1.4; }
    .decision-list { display: flex; flex-direction: column; gap: 0; }
    .decision-item { display: flex; gap: 12px; align-items: flex-start;
                     padding: 12px 0; border-bottom: 1px solid var(--border); }
    .decision-item:last-child { border-bottom: none; padding-bottom: 0; }
    .decision-priority { flex-shrink: 0; font-size: 10px; font-weight: 700;
                         padding: 3px 7px; border-radius: 10px;
                         text-transform: uppercase; letter-spacing: 0.4px; margin-top: 2px; }
    .decision-priority.high   { background: var(--critical-light); color: var(--critical); }
    .decision-priority.medium { background: var(--medium-light); color: #92400e; }
    .decision-priority.low    { background: var(--low-light); color: #166534; }
    .decision-body { flex: 1; }
    .decision-title  { font-size: 12px; font-weight: 600; color: var(--text);
                       margin-bottom: 3px; line-height: 1.4; }
    .decision-action { font-size: 11px; color: var(--text-muted); line-height: 1.4; }
    .decision-due { font-size: 10px; font-weight: 600; margin-top: 4px; }
    .decision-due.urgent { color: var(--critical); }
    .decision-due.normal { color: var(--text-muted); }
    .decision-due.tbd    { color: var(--text-light); }
    .watch-list { display: flex; flex-direction: column; gap: 8px; }
    .watch-item { padding: 10px 14px; border-radius: var(--radius-sm);
                  border: 1px solid var(--border); background: var(--surface-2);
                  display: flex; gap: 10px; align-items: flex-start; }
    .watch-icon { flex-shrink: 0; font-size: 13px; margin-top: 1px; }
    .watch-body { flex: 1; min-width: 0; }
    .watch-title { font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 2px; }
    .watch-risk  { font-size: 11px; color: var(--text-muted); line-height: 1.4; }
    .event-list { display: flex; flex-direction: column; gap: 8px; }
    .event-item { display: flex; gap: 12px; align-items: center; padding: 10px 12px;
                  border-radius: var(--radius-sm); border: 1px solid var(--border);
                  background: var(--surface-2); }
    .event-item.pm { background: var(--primary-light); border-color: #a5f3fc; }
    .event-date { flex-shrink: 0; width: 46px; text-align: center;
                  background: #fff; border-radius: var(--radius-sm); padding: 4px;
                  border: 1px solid var(--border); }
    .event-date .month { font-size: 9px; font-weight: 700; text-transform: uppercase;
                         color: var(--text-muted); }
    .event-date .day { font-size: 18px; font-weight: 800; line-height: 1.1;
                       color: var(--text); }
    .event-body { flex: 1; min-width: 0; }
    .event-title { font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 1px; }
    .event-note  { font-size: 11px; color: var(--text-muted); }
    .event-action-tag { flex-shrink: 0; font-size: 9px; font-weight: 700;
                        text-transform: uppercase; letter-spacing: 0.4px;
                        padding: 2px 6px; border-radius: 8px;
                        background: #0891b2; color: #fff; }
    .vendor-header { display: flex; align-items: center; justify-content: space-between;
                     margin-bottom: 16px; }
    .vendor-name { font-size: 16px; font-weight: 800; color: var(--text); }
    .vendor-score-big { font-size: 36px; font-weight: 900; color: var(--low);
                        line-height: 1; display: flex; align-items: baseline; gap: 4px; }
    .vendor-score-big .denom { font-size: 16px; color: var(--text-muted); font-weight: 400; }
    .scorecard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .score-label { font-size: 11px; color: var(--text-muted); margin-bottom: 5px; }
    .score-bar-row { display: flex; align-items: center; gap: 8px; }
    .score-bar-track { flex: 1; height: 8px; background: var(--border); border-radius: 4px;
                       overflow: hidden; }
    .score-bar-fill { height: 100%; border-radius: 4px; background: var(--low); }
    .score-bar-fill.warn { background: var(--yellow-badge); }
    .score-num { font-size: 12px; font-weight: 700; color: var(--text);
                 min-width: 24px; text-align: right; }
    .vendor-notes { margin-top: 14px; padding: 12px 14px; background: var(--surface-2);
                    border-radius: var(--radius-sm); border: 1px solid var(--border);
                    font-size: 11px; color: var(--text-muted); line-height: 1.5; }
    .flags-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px;
                  margin-bottom: 20px; }
    @media (max-width:900px) { .flags-grid { grid-template-columns: repeat(2,1fr); } }
    .flag-card { border: 1px solid var(--border); border-radius: var(--radius-sm);
                 padding: 12px 14px; background: var(--surface-2); }
    .flag-header { display: flex; align-items: center; justify-content: space-between;
                   margin-bottom: 8px; }
    .flag-label { font-size: 10px; font-weight: 700; text-transform: uppercase;
                  letter-spacing: 0.5px; color: var(--text-muted); }
    .flag-count { font-size: 22px; font-weight: 800; }
    .flag-count.red    { color: var(--critical); }
    .flag-count.orange { color: var(--high); }
    .flag-count.yellow { color: var(--medium); }
    .flag-count.blue   { color: var(--evidenced); }
    .flag-count.purple { color: var(--impl); }
    .flag-items { font-size: 11px; color: var(--text-muted); line-height: 1.6; }
    .flag-item::before { content: '—'; margin-right: 4px; color: var(--text-light); }
    .unavailable { padding: 16px; color: var(--text-muted); font-size: 12px;
                   font-style: italic; background: var(--surface-2);
                   border-radius: var(--radius-sm); }
    .next-run-bar { background: #0c1a2e; border-radius: var(--radius);
                    padding: 16px 24px; display: flex; align-items: center;
                    justify-content: space-between; margin-top: 24px;
                    flex-wrap: wrap; gap: 12px; }
    .next-run-label  { font-size: 10px; font-weight: 700; text-transform: uppercase;
                       letter-spacing: 0.6px; color: #475569; margin-bottom: 3px; }
    .next-run-text   { font-size: 14px; font-weight: 700; color: #f1f5f9; }
    .next-run-reason { font-size: 11px; color: #64748b; margin-top: 3px; }
    .next-run-intent { font-size: 12px; font-weight: 700; padding: 6px 14px;
                       border-radius: 20px; background: #1e3a5f; color: #93c5fd;
                       font-family: monospace; letter-spacing: 0.5px; }
    .status-bar { background: #fff8ed; border: 1px solid #fde68a;
                  border-left: 4px solid var(--yellow-badge); border-radius: var(--radius);
                  padding: 12px 20px; margin-bottom: 20px; font-size: 12px;
                  color: #78350f; line-height: 1.5; }
    footer { text-align: center; font-size: 11px; color: var(--text-light);
             padding: 20px 32px 32px; }
    /* ── PRIORITIES BANNER ── */
    .priorities-banner { background: #fff8ed; border: 1px solid #fde68a;
                         border-left: 4px solid var(--yellow-badge);
                         border-radius: var(--radius); padding: 14px 20px;
                         margin-bottom: 20px; }
    .priorities-banner h2 { font-size: 11px; font-weight: 800; color: #92400e;
                            text-transform: uppercase; letter-spacing: 0.7px;
                            margin-bottom: 10px; }
    .priority-items { display: flex; flex-direction: column; gap: 6px; }
    .priority-item { display: flex; gap: 10px; align-items: flex-start;
                     font-size: 12px; line-height: 1.4; }
    .priority-dot { flex-shrink: 0; width: 8px; height: 8px; border-radius: 50%;
                    margin-top: 4px; }
    .priority-dot.urgent { background: var(--critical); }
    .priority-dot.soon   { background: var(--medium); }
    .priority-text { color: var(--text); }
    .priority-date { flex-shrink: 0; font-size: 10px; font-weight: 700;
                     color: var(--text-muted); white-space: nowrap; }
    /* ── SCOPE CARD ── */
    .scope-tag { display: inline-block; padding: 3px 8px; border-radius: 6px;
                 font-size: 10px; font-weight: 600; margin: 2px 3px 2px 0;
                 background: var(--primary-light); color: #0e7490;
                 border: 1px solid #a5f3fc; }
    .scope-tag.workstream { background: var(--impl-light); color: #5b21b6;
                            border-color: #c4b5fd; }
    .scope-mission { font-size: 12px; color: var(--text); line-height: 1.5;
                     margin-bottom: 12px; }
    /* ── PEOPLE / STAKEHOLDER GRID ── */
    .person-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px,1fr));
                   gap: 8px; }
    .person-card { padding: 10px 14px; border: 1px solid var(--border);
                   border-radius: var(--radius-sm); background: var(--surface-2); }
    .person-name { font-size: 12px; font-weight: 700; color: var(--text); }
    .person-role { font-size: 11px; color: var(--text-muted); margin-top: 1px; }
    .person-org  { font-size: 10px; color: var(--text-light); margin-top: 1px; }
    .person-owns { font-size: 11px; color: var(--text-muted); margin-top: 6px;
                   padding-top: 6px; border-top: 1px solid var(--border);
                   line-height: 1.5; }
    .owns-label { font-size: 9px; font-weight: 700; text-transform: uppercase;
                  letter-spacing: 0.4px; color: var(--text-light); }
    .ownership-gap { background: var(--high-light); border: 1px solid #fdba74;
                     border-radius: var(--radius-sm); padding: 8px 12px;
                     font-size: 11px; color: #7c2d12; margin-top: 10px; }
    .ownership-gap .gap-label { font-size: 10px; font-weight: 700;
                                text-transform: uppercase; letter-spacing: 0.4px;
                                color: var(--high); margin-bottom: 4px; }
    /* ── COMMITMENTS ── */
    .commitment-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .commitment-table th { font-size: 10px; font-weight: 700; text-transform: uppercase;
                           letter-spacing: 0.4px; color: var(--text-muted);
                           padding: 6px 10px; border-bottom: 2px solid var(--border);
                           text-align: left; }
    .commitment-table td { padding: 9px 10px; border-bottom: 1px solid var(--border);
                           vertical-align: top; }
    .commitment-table tr:last-child td { border-bottom: none; }
    .commit-date { font-size: 11px; font-weight: 700; white-space: nowrap; }
    .commit-date.overdue { color: var(--critical); }
    .commit-date.soon    { color: var(--high); }
    .commit-date.future  { color: var(--text-muted); }
    .commit-item  { font-weight: 600; color: var(--text); line-height: 1.4; }
    .commit-owner { font-size: 11px; color: var(--text-muted); }
    .commit-owner.missing { color: var(--critical); font-weight: 600; }
    .commit-deps { font-size: 10px; color: var(--text-light); margin-top: 3px; }
    .section-sub-label { font-size: 10px; font-weight: 700; text-transform: uppercase;
                         letter-spacing: 0.5px; color: var(--text-muted);
                         margin: 14px 0 8px; display: flex; align-items: center; gap: 8px; }
    .section-sub-label::after { content:''; flex:1; height:1px; background:var(--border); }
    .soft-target-list { display: flex; flex-direction: column; gap: 4px; }
    .soft-target-item { font-size: 12px; color: var(--text-muted); padding: 4px 0;
                        border-bottom: 1px solid var(--border); display: flex;
                        gap: 10px; align-items: baseline; }
    .soft-target-item:last-child { border-bottom: none; }
    .soft-date { font-size: 11px; font-weight: 600; color: var(--text-muted);
                 white-space: nowrap; min-width: 80px; }
    /* ── EVIDENCE WINDOWS ── */
    .ev-window { padding: 10px 14px; border-radius: var(--radius-sm);
                 border: 1px solid var(--border); background: var(--surface-2);
                 margin-bottom: 8px; display: flex; gap: 12px; align-items: flex-start; }
    .ev-window:last-child { margin-bottom: 0; }
    .ev-status { flex-shrink: 0; font-size: 9px; font-weight: 700; padding: 2px 7px;
                 border-radius: 8px; text-transform: uppercase; letter-spacing: 0.3px;
                 margin-top: 2px; }
    .ev-status.scheduled  { background: var(--primary-light); color: #0e7490; }
    .ev-status.in-progress{ background: var(--impl-light); color: #5b21b6; }
    .ev-status.complete   { background: var(--low-light); color: var(--low); }
    .ev-status.overdue    { background: var(--critical-light); color: var(--critical); }
    .ev-window-body { flex: 1; }
    .ev-window-name { font-size: 12px; font-weight: 600; color: var(--text);
                      margin-bottom: 2px; }
    .ev-controls { font-size: 10px; color: var(--text-muted); font-family: monospace; }
    .ev-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
"""


# ---------------------------------------------------------------------------
# HTML escaping
# ---------------------------------------------------------------------------

def e(s: object) -> str:
    """HTML-escape and return a string."""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# Schema-agnostic data helpers
# ---------------------------------------------------------------------------

def _dig(d: dict, *keys: str, default: object = "") -> object:
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)  # type: ignore[assignment]
    return d if d is not None else default


def get_schema(run: dict) -> str:
    return str(run.get("schema_version", "1.1"))


def get_program_name(run: dict) -> str:
    return (run.get("program_name")
            or _dig(run, "run_manifest", "program_name")
            or run.get("_program_slug", "Unknown"))


def get_health(run: dict) -> str:
    return (run.get("overall_health")
            or _dig(run, "program_state", "overall_health")
            or "unknown").lower()


def get_phase(run: dict) -> str:
    return (run.get("phase")
            or _dig(run, "run_manifest", "phase")
            or _dig(run, "intake_output", "scope", "phase")
            or "")


def get_run_date(run: dict) -> str:
    return (run.get("run_date")
            or _dig(run, "run_manifest", "run_date")
            or "")


def get_pm_name(run: dict) -> str:
    pm = _dig(run, "run_manifest", "pm_name")
    if not pm:
        roster = _dig(run, "people", "roster", default=[])
        if not isinstance(roster, list):
            roster = []
        for p in roster:
            if isinstance(p, dict) and p.get("role", "").lower() in (
                    "program manager", "pm", "lead program manager", "pm / lead program manager"):
                pm = p.get("name", "")
                break
    return str(pm)


def get_one_line_status(run: dict) -> str:
    return (run.get("one_line_status")
            or _dig(run, "program_state", "one_line_status")
            or "")


def get_frameworks(run: dict) -> list[str]:
    raw = (run.get("scope") or {}).get("frameworks") or []
    if not raw:
        raw = _dig(run, "intake_output", "scope", "frameworks", default=[])
    result = []
    for item in (raw if isinstance(raw, list) else []):
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            result.append(item.get("name") or item.get("framework") or str(item))
    return result


def get_decision_queue(run: dict) -> list[dict]:
    mo = run.get("monitoring_output") or {}
    dq = mo.get("decision_queue") or []
    if not dq:
        # schema 2.0 uses commitments
        raw = run.get("commitments") or []
        dq = [{"item": c.get("title", c.get("item", "")),
               "action_needed": c.get("action", c.get("action_needed", "")),
               "owner": c.get("owner", ""),
               "due": c.get("due_date", c.get("due", "")),
               "priority": c.get("priority", "medium")}
              for c in raw if isinstance(c, dict)]
    return dq


def get_watch_list(run: dict) -> list[dict]:
    mo = run.get("monitoring_output") or {}
    return mo.get("watch_list") or []


def get_escalations(run: dict) -> list[dict]:
    mo = run.get("monitoring_output") or {}
    return mo.get("escalation_items") or []


def get_flags(run: dict) -> dict:
    return run.get("flags") or {}


def get_risk_register(run: dict) -> dict:
    rr = run.get("risk_register") or {}
    return rr if isinstance(rr, dict) else {}


def get_vendor_output(run: dict) -> dict:
    vo = run.get("vendor_output") or {}
    if isinstance(vo, list):
        return {}
    return vo


def get_people(run: dict) -> dict:
    return (run.get("people")
            or (run.get("intake_output") or {}).get("people")
            or {})


def get_calendar_events(run: dict) -> list[dict]:
    return run.get("calendar_events") or []


def get_next_run(run: dict) -> dict:
    return run.get("next_run_recommendation") or {}


def get_next_run_recommendation(run: dict) -> dict:
    """Alias with clear intent."""
    return get_next_run(run)


def get_scope(run: dict) -> dict:
    """Return scope dict from schema 2.0 (run.scope) or 1.1 (intake_output.scope)."""
    return (run.get("scope")
            or (run.get("intake_output") or {}).get("scope")
            or {})


def get_commitments(run: dict) -> dict:
    """Return commitments dict (schema 2.0 only; schema 1.1 uses decision_queue)."""
    raw = run.get("commitments") or {}
    if isinstance(raw, dict):
        return raw
    return {}


def get_evidence_windows(run: dict) -> list[dict]:
    """Return evidence_calendar.windows[] (schema 2.0)."""
    ec = run.get("evidence_calendar") or {}
    if isinstance(ec, dict):
        return ec.get("windows") or []
    return []


# ---------------------------------------------------------------------------
# Coverage normalisation (same logic as auditor_view_renderer._normalize_coverage)
# ---------------------------------------------------------------------------

def _normalize_coverage(run: dict) -> dict:
    cov = run.get("control_coverage") or {}
    if cov and cov.get("families"):
        return cov

    # 62443-style control_coverage_matrix
    ccm = run.get("control_coverage_matrix") or {}
    if not ccm:
        return {}

    cs = ccm.get("coverage_summary") or {}
    controls = ccm.get("controls") or []

    groups: dict[str, dict] = defaultdict(lambda: {
        "evidenced": 0, "implemented_no_evidence": 0, "gap": 0, "not_applicable": 0,
    })
    status_map = {"✓": "evidenced", "~": "implemented_no_evidence", "✗": "gap"}
    for ctrl in controls:
        prefix = (ctrl.get("control_id") or "").split("-")[0] or "Other"
        key = status_map.get(ctrl.get("status", ""), "gap")
        groups[prefix][key] += 1

    families = []
    for prefix, counts in sorted(groups.items()):
        total = sum(counts.values())
        families.append({
            "family": prefix,
            "total": total,
            "evidenced": counts["evidenced"],
            "implemented_no_evidence": counts["implemented_no_evidence"],
            "gap": counts["gap"],
            "not_applicable": counts["not_applicable"],
        })

    return {
        "framework": ccm.get("framework", "IEC 62443-4-2"),
        "assessment_date": ccm.get("assessment_date", ""),
        "families": families,
        "totals": {
            "total": cs.get("total_controls", 0),
            "evidenced": cs.get("evidenced", 0),
            "implemented_no_evidence": cs.get("implemented_no_evidence", 0),
            "gap": cs.get("gap", 0),
            "not_applicable": cs.get("not_applicable", 0),
        },
    }


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _health_badge(health: str) -> str:
    labels = {"yellow": "Yellow", "red": "Red",
               "green": "Green", "unknown": "Unknown"}
    lbl = labels.get(health, health.title())
    cls = health if health in labels else "unknown"
    return (f'<div class="health-badge {cls}">'
            f'<div class="health-dot"></div>{e(lbl)}</div>')


def render_header(run: dict) -> str:
    name = get_program_name(run)
    health = get_health(run)
    phase = get_phase(run)
    run_date = get_run_date(run)
    pm = get_pm_name(run)
    frameworks = get_frameworks(run)
    subtitle = " &nbsp;·&nbsp; ".join(e(f) for f in frameworks[:2]) if frameworks else e(phase)
    badge = _health_badge(health)
    run_meta = ""
    if run_date:
        run_meta += f'<div class="run-meta"><div class="label">Data as of</div><div class="value">{e(run_date)}</div></div>'
    if pm:
        run_meta += f'<div class="run-meta"><div class="label">PM</div><div class="value">{e(pm)}</div></div>'
    # Initials for logo
    words = name.split()
    initials = "".join(w[0] for w in words if w)[:3].upper()
    return f"""<header class="header">
  <div class="header-left">
    <div class="header-logo">{e(initials)}</div>
    <div>
      <div class="header-title">{e(name)}</div>
      <div class="header-subtitle">{subtitle}</div>
    </div>
  </div>
  <div class="header-right">
    {badge}
    {run_meta}
  </div>
</header>"""


def render_staleness_notice(run: dict) -> str:
    nrr = get_next_run(run)
    suggested = nrr.get("suggested_date", "")
    run_date = get_run_date(run)
    if not suggested or not run_date:
        return ""
    try:
        import datetime
        overdue = datetime.date.fromisoformat(suggested) < datetime.date.today()
        if overdue:
            return (f'<div class="staleness-notice">'
                    f'<strong>Note:</strong> This dashboard was generated from data last '
                    f'updated {e(run_date)}. A pipeline run was recommended by '
                    f'{e(suggested)}. Data may not reflect current program state.</div>')
    except ValueError:
        pass
    return ""


def render_status_bar(run: dict) -> str:
    status = get_one_line_status(run)
    if not status:
        return ""
    return f'<div class="status-bar">{e(status)}</div>'


def render_escalations(run: dict) -> str:
    items = get_escalations(run)
    if not items:
        return ""
    rows = ""
    for i, item in enumerate(items[:6], 1):
        title = e(item.get("title") or item.get("item") or "Escalation")
        detail = e(item.get("detail") or item.get("description") or "")
        action = e(item.get("action_needed") or item.get("action") or "")
        rows += f"""<div class="escalation-item">
    <div class="escalation-num">{i}</div>
    <div>
      <div class="escalation-text"><strong>{title}</strong>{"<br>" + detail if detail else ""}</div>
      {"<div class='escalation-action'>" + action + "</div>" if action else ""}
    </div>
  </div>"""
    return f"""<div class="escalation-banner">
  <h2>⚠ Escalation Required</h2>
  <div class="escalation-grid">{rows}</div>
</div>"""


def render_stats_row(run: dict) -> str:
    flags = get_flags(run)
    rr = get_risk_register(run)
    dq = get_decision_queue(run)
    watch = get_watch_list(run)
    vo = get_vendor_output(run)

    owner_gaps = len(flags.get("owner_needed") or [])
    open_rr = rr.get("open") or {}
    critical_risks = int(open_rr.get("critical") or 0)
    high_risks = int(open_rr.get("high") or 0)
    decisions = len(dq)
    watch_count = len(watch)

    # vendor score
    sc = (vo.get("scorecard") or {})
    vendor_score = sc.get("overall")
    vendor_name = vo.get("vendor_name", "Vendor")

    cards = []

    if critical_risks > 0:
        pct = 100
        cards.append(f"""<div class="stat-card critical">
  <div class="stat-label">Critical Risks</div>
  <div class="stat-value">{critical_risks}</div>
  <div class="stat-sub">Require immediate action</div>
  <div class="stat-bar"><div class="stat-bar-fill" style="width:{pct}%;background:var(--critical)"></div></div>
</div>""")
    if high_risks > 0:
        mx = max(high_risks, 1)
        pct = min(100, int(high_risks / mx * 100))
        cards.append(f"""<div class="stat-card warning">
  <div class="stat-label">High Risks</div>
  <div class="stat-value">{high_risks}</div>
  <div class="stat-sub">Require formal POA&amp;M</div>
  <div class="stat-bar"><div class="stat-bar-fill" style="width:{pct}%;background:var(--high)"></div></div>
</div>""")
    if owner_gaps > 0:
        cards.append(f"""<div class="stat-card warning">
  <div class="stat-label">Owner Gaps</div>
  <div class="stat-value">{owner_gaps}</div>
  <div class="stat-sub">Unassigned responsibilities</div>
  <div class="stat-bar"><div class="stat-bar-fill" style="width:100%;background:var(--high)"></div></div>
</div>""")
    if decisions > 0:
        cards.append(f"""<div class="stat-card info">
  <div class="stat-label">Open Decisions</div>
  <div class="stat-value">{decisions}</div>
  <div class="stat-sub">In decision queue</div>
  <div class="stat-bar"><div class="stat-bar-fill" style="width:75%;background:var(--primary)"></div></div>
</div>""")
    if watch_count > 0:
        cards.append(f"""<div class="stat-card neutral">
  <div class="stat-label">Watch Items</div>
  <div class="stat-value">{watch_count}</div>
  <div class="stat-sub">Active monitoring</div>
  <div class="stat-bar"><div class="stat-bar-fill" style="width:60%;background:var(--text-muted)"></div></div>
</div>""")
    if vendor_score and not cards or (vendor_score and len(cards) < 5):
        pct = int(float(vendor_score) / 5 * 100)
        cards.append(f"""<div class="stat-card ok">
  <div class="stat-label">{e(vendor_name)} Score</div>
  <div class="stat-value">{vendor_score}</div>
  <div class="stat-sub">out of 5.0 — {e(sc.get('trend',''))}</div>
  <div class="stat-bar"><div class="stat-bar-fill" style="width:{pct}%;background:var(--low)"></div></div>
</div>""")

    if not cards:
        return ""

    return f'<div class="stats-row">{"".join(cards[:5])}</div>'


def render_coverage_section(run: dict) -> str:
    cov = _normalize_coverage(run)
    if not cov or not cov.get("families"):
        return f"""<div class="section-label">Control Coverage</div>
<div class="card" style="margin-bottom:20px">
  <div class="card-header"><div class="card-title">Control Coverage Status</div></div>
  <div class="card-body"><div class="unavailable">[DATA UNAVAILABLE — runs/{run.get('_program_slug','')}/latest.json → control_coverage]<br>Run a coverage assessment to populate this section.</div></div>
</div>"""

    families = cov.get("families") or []
    totals = cov.get("totals") or {}
    framework = cov.get("framework", "")
    adate = cov.get("assessment_date", "")

    total = int(totals.get("total") or sum(f.get("total", 0) for f in families))
    evidenced = int(totals.get("evidenced") or sum(f.get("evidenced", 0) for f in families))
    impl = int(totals.get("implemented_no_evidence")
               or sum(f.get("implemented_no_evidence", 0) for f in families))
    gap = int(totals.get("gap") or sum(f.get("gap", 0) for f in families))
    na = int(totals.get("not_applicable") or sum(f.get("not_applicable", 0) for f in families))
    denom = max(total - na, 1)
    ev_pct = round(evidenced / denom * 100)
    impl_pct = round(impl / denom * 100)
    gap_pct = round(gap / denom * 100)

    # coverage bar
    bar = f"""<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-bottom:4px;">
  <span>{total} controls assessed &nbsp;·&nbsp;
    <span style="color:var(--evidenced);font-weight:700;">{evidenced} evidenced ({ev_pct}%)</span> &nbsp;·&nbsp;
    <span style="color:var(--impl);font-weight:700;">{impl} impl/no evidence ({impl_pct}%)</span> &nbsp;·&nbsp;
    <span style="color:var(--gap);font-weight:700;">{gap} gaps ({gap_pct}%)</span>
  </span>
</div>
<div class="coverage-bar-track">
  <div class="coverage-bar-seg" style="width:{ev_pct}%;background:var(--evidenced)"></div>
  <div class="coverage-bar-seg" style="width:{impl_pct}%;background:var(--impl)"></div>
  <div class="coverage-bar-seg" style="width:{gap_pct}%;background:var(--gap)"></div>
</div>"""

    # family table
    rows = ""
    for fam in families:
        fname = e(fam.get("name") or fam.get("family") or "—")
        ftotal = int(fam.get("total") or 0)
        fev = int(fam.get("evidenced") or 0)
        fim = int(fam.get("implemented_no_evidence") or 0)
        fgap = int(fam.get("gap") or 0)
        fna = int(fam.get("not_applicable") or 0)
        fdenom = max(ftotal - fna, 1)
        fpct = round((fev + fim) / fdenom * 100)
        gap_style = ' style="color:var(--critical);font-weight:600;"' if fgap > 0 else ""
        rows += f"""<tr>
  <td>{fname}</td><td>{ftotal}</td>
  <td style="color:var(--evidenced);font-weight:600">{fev}</td>
  <td style="color:var(--impl);font-weight:600">{fim}</td>
  <td{gap_style}>{fgap}</td>
  <td>{fna}</td>
  <td>{fpct}%</td>
</tr>"""

    # totals row
    rows += f"""<tr class="totals-row">
  <td>TOTAL</td><td>{total}</td>
  <td style="color:var(--evidenced)">{evidenced}</td>
  <td style="color:var(--impl)">{impl}</td>
  <td style="color:var(--gap)">{gap}</td>
  <td>{na}</td>
  <td>{round((evidenced+impl)/denom*100)}%</td>
</tr>"""

    badge_txt = f"{framework}" if framework else f"{len(families)} families"
    sub = f" &nbsp;·&nbsp; {e(adate)}" if adate else ""
    return f"""<div class="section-label">Control Coverage{sub}</div>
<div class="card" style="margin-bottom:20px;">
  <div class="card-header">
    <div class="card-title">Coverage Matrix</div>
    <div class="card-badge{"" if gap==0 else " warn"}">{e(badge_txt)}</div>
  </div>
  <div class="card-body">
    {bar}
    <table class="cov-table" style="margin-top:16px;">
      <thead><tr>
        <th>Family / Category</th><th>Total</th><th>Evidenced</th>
        <th>Impl/No Ev</th><th>Gap</th><th>N/A</th><th>Coverage</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


def _donut_svg(critical: int, high: int, medium: int, low: int) -> str:
    total = max(critical + high + medium + low, 1)
    circ = 2 * math.pi * 50  # r=50
    offsets = [0.0]
    colors = ["#dc2626", "#ea580c", "#ca8a04", "#16a34a"]
    counts = [critical, high, medium, low]
    segs = ""
    for i, (c, color) in enumerate(zip(counts, colors)):
        dash = circ * c / total
        offset = -offsets[-1]
        segs += f'<circle cx="65" cy="65" r="50" fill="none" stroke="{color}" stroke-width="18" stroke-dasharray="{dash:.2f} {circ - dash:.2f}" stroke-dashoffset="{offset:.2f}"/>'
        offsets.append(offsets[-1] + dash)
    return f"""<svg width="130" height="130" viewBox="0 0 130 130">
  <circle cx="65" cy="65" r="50" fill="none" stroke="#e2e8f0" stroke-width="18"/>
  {segs}
</svg>"""


def render_risk_register(run: dict) -> str:
    rr = get_risk_register(run)
    if not rr:
        return f"""<div class="card">
  <div class="card-header"><div class="card-title">Risk Register</div></div>
  <div class="card-body"><div class="unavailable">[DATA UNAVAILABLE — risk_register not present]</div></div>
</div>"""

    open_counts = rr.get("open") or {}
    critical = int(open_counts.get("critical") or 0)
    high = int(open_counts.get("high") or 0)
    medium = int(open_counts.get("medium") or 0)
    low = int(open_counts.get("low") or 0)
    total_open = critical + high + medium + low

    donut = _donut_svg(critical, high, medium, low)
    mx = max(critical, high, medium, low, 1)
    legend = ""
    for label, count, color in [
        ("Critical", critical, "#dc2626"),
        ("High", high, "#ea580c"),
        ("Medium", medium, "#ca8a04"),
        ("Low", low, "#16a34a"),
    ]:
        pct = int(count / mx * 100) if mx > 0 else 0
        legend += f"""<div class="risk-legend-item">
  <div class="risk-legend-dot" style="background:{color}"></div>
  <div class="risk-legend-label">{label}</div>
  <div class="risk-legend-bar-track"><div class="risk-legend-bar" style="width:{pct}%;background:{color}"></div></div>
  <div class="risk-legend-count" style="color:{color}">{count}</div>
</div>"""

    # top 3 items
    items = rr.get("items") or []
    open_items = [it for it in items if isinstance(it, dict)
                  and str(it.get("status", "open")).lower() != "closed"][:3]
    top_items = ""
    for it in open_items:
        sev = str(it.get("severity") or "medium").lower()
        sev_colors = {"critical": ("var(--critical-light)", "#fca5a5", "var(--critical)"),
                      "high": ("var(--high-light)", "#fdba74", "var(--high)"),
                      "medium": ("var(--medium-light)", "#fde047", "var(--medium)"),
                      "low": ("var(--low-light)", "#86efac", "var(--low)")}
        bg, border, fc = sev_colors.get(sev, sev_colors["medium"])
        rid = e(it.get("id") or "")
        title = e(it.get("title") or "")
        top_items += f"""<div style="padding:8px 12px;background:{bg};border-radius:var(--radius-sm);border:1px solid {border};">
  <div style="font-size:10px;font-weight:700;color:{fc};font-family:monospace;margin-bottom:3px;">{rid} · {sev.title()}</div>
  <div style="font-size:12px;line-height:1.4;">{title}</div>
</div>"""

    badge = f"{total_open} Open"
    badge_cls = " warn" if critical > 0 else ""
    return f"""<div class="card">
  <div class="card-header">
    <div class="card-title">Risk Register</div>
    <div class="card-badge{badge_cls}">{badge}</div>
  </div>
  <div class="card-body">
    <div class="risk-chart-grid">
      <div class="donut-wrap">{donut}<div class="donut-center"><div class="big">{total_open}</div><div class="sm">Open</div></div></div>
      <div class="risk-legend">{legend}</div>
    </div>
    {"<div style='margin-top:18px;padding-top:14px;border-top:1px solid var(--border);'><div style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.4px;color:var(--text-muted);margin-bottom:10px;'>Open Items</div><div style='display:flex;flex-direction:column;gap:8px;'>" + top_items + "</div></div>" if top_items else ""}
  </div>
</div>"""


def render_decision_queue(run: dict) -> str:
    dq = get_decision_queue(run)
    if not dq:
        return ""
    rows = ""
    for item in dq[:8]:
        if not isinstance(item, dict):
            continue
        title = e(item.get("item") or item.get("title") or "")
        action = e(item.get("action_needed") or item.get("action") or "")
        due = str(item.get("due") or "")
        priority = str(item.get("priority") or "medium").lower()
        priority_cls = "high" if priority == "high" else ("low" if priority == "low" else "medium")
        due_cls = "tbd" if not due or "TBD" in due.upper() or "DATE NEEDED" in due.upper() else "urgent" if priority == "high" else "normal"
        rows += f"""<div class="decision-item">
  <div class="decision-priority {priority_cls}">{priority.title()}</div>
  <div class="decision-body">
    <div class="decision-title">{title}</div>
    {"<div class='decision-action'>" + action + "</div>" if action else ""}
    {"<div class='decision-due " + due_cls + "'>Due: " + e(due) + "</div>" if due else ""}
  </div>
</div>"""

    badge_cls = " warn" if any(
        str((d.get("priority") or "")).lower() == "high" for d in dq
    ) else ""
    return f"""<div class="card">
  <div class="card-header">
    <div class="card-title">Decision Queue</div>
    <div class="card-badge{badge_cls}">{len(dq)} Items</div>
  </div>
  <div class="card-body">
    <div class="decision-list">{rows}</div>
  </div>
</div>"""


def render_watch_list(run: dict) -> str:
    wl = get_watch_list(run)
    if not wl:
        return ""
    rows = ""
    icons = {"red": "🔴", "critical": "🔴", "high": "🟡", "yellow": "🟡",
             "medium": "🟡", "low": "⚪", "green": "🟢"}
    for item in wl[:8]:
        if not isinstance(item, dict):
            continue
        title = e(item.get("title") or item.get("item") or "")
        risk = e(item.get("risk") or item.get("description") or item.get("detail") or "")
        severity = str(item.get("severity") or item.get("priority") or "medium").lower()
        icon = icons.get(severity, "🟡")
        bg = ""
        if severity in ("red", "critical"):
            bg = " style='background:var(--critical-light);border-color:#fca5a5;'"
        rows += f"""<div class="watch-item"{bg}>
  <div class="watch-icon">{icon}</div>
  <div class="watch-body">
    <div class="watch-title">{title}</div>
    {"<div class='watch-risk'>" + risk + "</div>" if risk else ""}
  </div>
</div>"""

    return f"""<div class="card">
  <div class="card-header">
    <div class="card-title">Watch List</div>
    <div class="card-badge">{len(wl)} Items</div>
  </div>
  <div class="card-body">
    <div class="watch-list">{rows}</div>
  </div>
</div>"""


def render_calendar(run: dict) -> str:
    events = get_calendar_events(run)
    if not events:
        return ""
    rows = ""
    for ev in events[:10]:
        if not isinstance(ev, dict):
            continue
        title = e(ev.get("title") or "")
        raw_date = str(ev.get("date") or "")
        note = e(ev.get("notes") or ev.get("note") or "")
        owner = e(ev.get("owner") or "")
        pm_action = ev.get("pm_action_required") or False
        try:
            from datetime import date as ddate
            d = ddate.fromisoformat(raw_date)
            month = d.strftime("%b").upper()
            day = str(d.day)
        except (ValueError, TypeError):
            month = "TBD"
            day = "—"
        item_cls = "pm" if pm_action else ""
        tag = '<div class="event-action-tag">PM Action</div>' if pm_action else ""
        sub = note or owner
        rows += f"""<div class="event-item {item_cls}">
  <div class="event-date"><div class="month">{month}</div><div class="day">{day}</div></div>
  <div class="event-body">
    <div class="event-title">{title}</div>
    {"<div class='event-note'>" + sub + "</div>" if sub else ""}
  </div>
  {tag}
</div>"""

    return f"""<div class="card">
  <div class="card-header">
    <div class="card-title">Evidence Calendar</div>
    <div class="card-badge">{len(events)} Events</div>
  </div>
  <div class="card-body">
    <div class="event-list">{rows}</div>
  </div>
</div>"""


def render_vendor_scorecard(run: dict) -> str:
    vo = get_vendor_output(run)
    if not vo:
        return ""
    sc = vo.get("scorecard") or {}
    vendor_name = vo.get("vendor_name") or "Vendor"
    overall = sc.get("overall")
    if overall is None:
        return ""
    trend = str(sc.get("trend") or "")
    notes = e(sc.get("notes") or "")

    def score_bar(label: str, key: str) -> str:
        val = sc.get(key) or 0
        pct = int(float(val) / 5 * 100)
        warn_cls = " warn" if float(val) < 4 else ""
        return f"""<div>
  <div class="score-label">{e(label)}</div>
  <div class="score-bar-row">
    <div class="score-bar-track"><div class="score-bar-fill{warn_cls}" style="width:{pct}%"></div></div>
    <div class="score-num">{val}/5</div>
  </div>
</div>"""

    return f"""<div class="card">
  <div class="card-header">
    <div class="card-title">Vendor Scorecard</div>
    <div class="card-badge">{e(trend.title()) or "Scored"}</div>
  </div>
  <div class="card-body">
    <div class="vendor-header">
      <div class="vendor-name">{e(vendor_name)}</div>
      <div>
        <div class="vendor-score-big">{overall}<span class="denom">/5</span></div>
      </div>
    </div>
    <div class="scorecard-grid">
      {score_bar("Schedule Adherence", "schedule_adherence")}
      {score_bar("Responsiveness", "responsiveness")}
      {score_bar("Deliverable Quality", "deliverable_quality")}
      {score_bar("Comm. Proactivity", "communication_proactivity")}
    </div>
    {"<div class='vendor-notes'>" + notes + "</div>" if notes else ""}
  </div>
</div>"""


def render_flags(run: dict) -> str:
    flags = get_flags(run)
    if not flags:
        return ""

    flag_defs = [
        ("owner_needed", "Owner Needed", "red"),
        ("date_needed", "Date Needed", "orange"),
        ("inferred", "Inferred", "yellow"),
        ("unclear", "Unclear / Verify", "orange"),
        ("conflicts", "Conflicts", "red"),
        ("insufficient_data", "Insufficient Data", "blue"),
        ("one_way_door", "One-Way Door", "purple"),
    ]

    cards = ""
    for key, label, color in flag_defs:
        items = flags.get(key) or []
        if not items:
            continue
        item_html = ""
        for it in items[:6]:
            item_html += f'<div class="flag-item">{e(it if isinstance(it, str) else str(it))}</div>'
        cards += f"""<div class="flag-card">
  <div class="flag-header">
    <div class="flag-label">{label}</div>
    <div class="flag-count {color}">{len(items)}</div>
  </div>
  <div class="flag-items">{item_html}</div>
</div>"""

    if not cards:
        return ""
    return f"""<div class="section-label">Flags</div>
<div class="flags-grid">{cards}</div>"""


def render_next_run(run: dict) -> str:
    nrr = get_next_run(run)
    if not nrr:
        return ""
    date_str = e(nrr.get("suggested_date") or "")
    intent = e(nrr.get("suggested_intent") or "")
    reason = e(nrr.get("reason") or "")
    return f"""<div class="next-run-bar">
  <div>
    <div class="next-run-label">Next pipeline refresh</div>
    <div class="next-run-text">{date_str or "See reason below"}</div>
    {"<div class='next-run-reason'>" + reason + "</div>" if reason else ""}
  </div>
  {"<div class='next-run-intent'>INTENT: " + intent + "</div>" if intent else ""}
</div>"""


# ---------------------------------------------------------------------------
# New rich section renderers
# ---------------------------------------------------------------------------

def render_scope_card(run: dict) -> str:
    scope = get_scope(run)
    if not scope:
        return ""
    mission = e(scope.get("mission") or "")
    in_scope = scope.get("in_scope") or []
    out_of_scope = scope.get("out_of_scope") or []
    workstreams = scope.get("workstreams") or []
    frameworks = get_frameworks(run)

    fw_tags = "".join(
        f'<span class="scope-tag">{e(f)}</span>' for f in frameworks[:4]
    )
    in_scope_tags = ""
    for item in in_scope[:10]:
        label = item if isinstance(item, str) else (item.get("name") or str(item))
        in_scope_tags += f'<span class="scope-tag">{e(label)}</span>'
    ws_tags = "".join(
        f'<span class="scope-tag workstream">{e(ws if isinstance(ws,str) else ws.get("name",str(ws)))}</span>'
        for ws in workstreams[:6]
    )
    oos_tags = ""
    for item in out_of_scope[:6]:
        label = item if isinstance(item, str) else (item.get("name") or str(item))
        oos_tags += f'<span class="scope-tag" style="background:var(--surface-2);color:var(--text-muted);border-color:var(--border);">{e(label)}</span>'

    body = ""
    if mission:
        body += f'<p class="scope-mission">{mission}</p>'
    if fw_tags:
        body += f'<div style="margin-bottom:10px;"><div class="section-sub-label">Frameworks</div><div>{fw_tags}</div></div>'
    if in_scope_tags:
        body += f'<div style="margin-bottom:10px;"><div class="section-sub-label">In Scope</div><div>{in_scope_tags}</div></div>'
    if ws_tags:
        body += f'<div style="margin-bottom:10px;"><div class="section-sub-label">Workstreams</div><div>{ws_tags}</div></div>'
    if oos_tags:
        body += f'<div><div class="section-sub-label">Out of Scope</div><div>{oos_tags}</div></div>'

    if not body:
        return ""
    return f"""<div class="card">
  <div class="card-header">
    <div class="card-title">Program Scope</div>
    {"<div class='card-badge'>" + str(len(in_scope)) + " products in scope</div>" if in_scope else ""}
  </div>
  <div class="card-body">{body}</div>
</div>"""


def render_stakeholder_grid(run: dict) -> str:
    people = get_people(run)
    roster = people.get("roster") or []
    if not roster:
        return ""

    ownership_gaps = people.get("ownership_gaps") or []
    stakeholder_notes = e(people.get("stakeholder_notes") or "")

    cards = ""
    for person in roster:
        if not isinstance(person, dict):
            continue
        name = e(person.get("name") or "")
        role = e(person.get("role") or "")
        org = e(person.get("org") or "")
        owns = person.get("owns") or []
        notes = e(person.get("notes") or "")
        if not name:
            continue
        owns_html = ""
        if owns:
            bullets = "".join(
                f'<div>· {e(o if isinstance(o, str) else str(o))}</div>'
                for o in owns[:4]
            )
            owns_html = f'<div class="person-owns"><div class="owns-label">Owns</div>{bullets}</div>'
        cards += f"""<div class="person-card">
  <div class="person-name">{name}</div>
  <div class="person-role">{role}</div>
  {"<div class='person-org'>" + org + "</div>" if org else ""}
  {owns_html}
  {"<div style='font-size:10px;color:var(--text-light);margin-top:4px;'>" + notes + "</div>" if notes else ""}
</div>"""

    gaps_html = ""
    if ownership_gaps:
        gap_items = "".join(
            f'<div>· {e(g if isinstance(g, str) else str(g))}</div>'
            for g in ownership_gaps
        )
        gaps_html = f'<div class="ownership-gap" style="margin-top:12px;"><div class="gap-label">[OWNER NEEDED] {len(ownership_gaps)} gap{"s" if len(ownership_gaps)!=1 else ""}</div>{gap_items}</div>'

    notes_html = f'<div style="margin-top:10px;font-size:11px;color:var(--text-muted);padding:10px;background:var(--surface-2);border-radius:var(--radius-sm);border:1px solid var(--border);">{stakeholder_notes}</div>' if stakeholder_notes else ""

    badge = f"{len(roster)} people"
    return f"""<div class="card">
  <div class="card-header">
    <div class="card-title">Stakeholders</div>
    <div class="card-badge">{badge}</div>
  </div>
  <div class="card-body">
    <div class="person-grid">{cards}</div>
    {gaps_html}
    {notes_html}
  </div>
</div>"""


def render_priorities_banner(run: dict) -> str:
    """Surface items due within 14 days across commitments, calendar, and high-priority decisions."""
    from datetime import date as ddate, timedelta
    cutoff_14 = ddate.today() + timedelta(days=14)
    cutoff_7 = ddate.today() + timedelta(days=7)
    today = ddate.today()

    items: list[tuple[ddate, str, str, str]] = []  # (date, label, owner, urgency)

    # Hard deadlines from commitments
    comms = get_commitments(run)
    for dl in (comms.get("hard_deadlines") or []):
        if not isinstance(dl, dict):
            continue
        raw = str(dl.get("date") or "")
        try:
            d = ddate.fromisoformat(raw)
        except ValueError:
            continue
        if today <= d <= cutoff_14:
            label = str(dl.get("item") or "")
            owner = str(dl.get("owner") or "")
            urgency = "urgent" if d <= cutoff_7 else "soon"
            items.append((d, label, owner, urgency))

    # Calendar events within 7 days
    for ev in get_calendar_events(run):
        if not isinstance(ev, dict):
            continue
        raw = str(ev.get("date") or "")
        try:
            d = ddate.fromisoformat(raw)
        except ValueError:
            continue
        if today <= d <= cutoff_7 and ev.get("pm_action_required"):
            label = str(ev.get("title") or "")
            owner = str(ev.get("owner") or "")
            items.append((d, label, owner, "urgent"))

    # High-priority decisions (no date filter — always surfaces them)
    for dq in get_decision_queue(run):
        if not isinstance(dq, dict):
            continue
        if str(dq.get("priority") or "").lower() == "high":
            label = str(dq.get("item") or dq.get("title") or "")
            owner = str(dq.get("owner") or "")
            items.append((today, label, owner, "urgent"))

    if not items:
        return ""

    # Deduplicate on label, sort by date
    seen: set[str] = set()
    deduped = []
    for it in sorted(items, key=lambda x: x[0]):
        if it[1] not in seen:
            seen.add(it[1])
            deduped.append(it)

    rows = ""
    for d, label, owner, urgency in deduped[:8]:
        dot_cls = "urgent" if urgency == "urgent" else "soon"
        date_str = d.strftime("%b %-d") if d != today else "Today"
        owner_txt = f" · {e(owner)}" if owner else ""
        rows += f"""<div class="priority-item">
  <div class="priority-dot {dot_cls}"></div>
  <div class="priority-text">{e(label)}{owner_txt}</div>
  <div class="priority-date">{date_str}</div>
</div>"""

    count = len(deduped)
    return f"""<div class="priorities-banner">
  <h2>Priorities — Next 2 Weeks ({count} item{"s" if count!=1 else ""})</h2>
  <div class="priority-items">{rows}</div>
</div>"""


def render_commitments(run: dict) -> str:
    comms = get_commitments(run)
    if not comms:
        return ""

    hard = comms.get("hard_deadlines") or []
    soft = comms.get("soft_targets") or []
    recurring = comms.get("recurring_obligations") or []

    if not hard and not soft and not recurring:
        return ""

    from datetime import date as ddate
    today = ddate.today()

    def date_cls(raw: str) -> str:
        try:
            d = ddate.fromisoformat(raw)
            if d < today:
                return "overdue"
            if (d - today).days <= 14:
                return "soon"
        except ValueError:
            pass
        return "future"

    hard_rows = ""
    for dl in hard:
        if not isinstance(dl, dict):
            continue
        item = e(dl.get("item") or "")
        raw_date = str(dl.get("date") or "")
        owner = dl.get("owner") or ""
        deps = dl.get("dependencies") or []
        notes = e(dl.get("notes") or "")
        dcls = date_cls(raw_date)
        owner_cls = "missing" if not owner else ""
        owner_txt = e(owner) if owner else "[OWNER NEEDED]"
        dep_txt = e(", ".join(str(d) for d in deps[:3])) if deps else ""
        hard_rows += f"""<tr>
  <td><span class="commit-date {dcls}">{e(raw_date)}</span></td>
  <td><div class="commit-item">{item}</div>{"<div class='commit-deps'>Depends on: " + dep_txt + "</div>" if dep_txt else ""}{"<div style='font-size:10px;color:var(--text-light);margin-top:2px;'>" + notes[:80] + "…</div>" if notes and len(notes)>10 else ""}</td>
  <td><span class="commit-owner {owner_cls}">{owner_txt}</span></td>
</tr>"""

    hard_section = ""
    if hard_rows:
        hard_section = f"""<table class="commitment-table">
  <thead><tr><th>Date</th><th>Commitment</th><th>Owner</th></tr></thead>
  <tbody>{hard_rows}</tbody>
</table>"""

    soft_section = ""
    if soft:
        soft_items = ""
        for st in soft:
            if isinstance(st, dict):
                label = e(st.get("item") or st.get("target") or "")
                raw_d = str(st.get("date") or "")
                owner = e(st.get("owner") or "")
                soft_items += f'<div class="soft-target-item"><span class="soft-date">{e(raw_d)}</span><span>{label}{" · " + owner if owner else ""}</span></div>'
            elif isinstance(st, str):
                soft_items += f'<div class="soft-target-item"><span class="soft-date">—</span><span>{e(st)}</span></div>'
        if soft_items:
            soft_section = f'<div class="section-sub-label">Soft Targets</div><div class="soft-target-list">{soft_items}</div>'

    rec_section = ""
    if recurring:
        rec_items = ""
        for r in recurring:
            if isinstance(r, dict):
                label = e(r.get("item") or r.get("obligation") or "")
                freq = e(r.get("frequency") or r.get("cadence") or "")
                owner = e(r.get("owner") or "")
                rec_items += f'<div class="soft-target-item"><span class="soft-date">{freq}</span><span>{label}{" · " + owner if owner else ""}</span></div>'
            elif isinstance(r, str):
                rec_items += f'<div class="soft-target-item"><span class="soft-date">Recurring</span><span>{e(r)}</span></div>'
        if rec_items:
            rec_section = f'<div class="section-sub-label">Recurring Obligations</div><div class="soft-target-list">{rec_items}</div>'

    badge_warn = any(not (dl.get("owner") if isinstance(dl, dict) else True) for dl in hard)
    badge_cls = " warn" if badge_warn else ""
    badge_txt = f"{len(hard)} hard deadline{'s' if len(hard)!=1 else ''}"

    return f"""<div class="card" style="margin-bottom:20px;">
  <div class="card-header">
    <div class="card-title">Commitments &amp; Deadlines</div>
    <div class="card-badge{badge_cls}">{badge_txt}</div>
  </div>
  <div class="card-body">
    {hard_section}
    {soft_section}
    {rec_section}
  </div>
</div>"""


def render_evidence_windows(run: dict) -> str:
    windows = get_evidence_windows(run)
    if not windows:
        return ""

    from datetime import date as ddate
    today = ddate.today()

    def win_status_cls(status: str, due: str) -> str:
        s = status.lower().replace(" ", "-") if status else ""
        if s in ("complete", "completed"):
            return "complete"
        if s in ("in-progress", "in_progress"):
            return "in-progress"
        try:
            if ddate.fromisoformat(due) < today and s not in ("complete",):
                return "overdue"
        except ValueError:
            pass
        return "scheduled"

    rows = ""
    for win in windows:
        if not isinstance(win, dict):
            continue
        name = e(win.get("name") or "")
        controls = e(win.get("controls") or "")
        due = str(win.get("due_date") or "")
        status = str(win.get("status") or "scheduled")
        owner = e(win.get("owner") or "")
        scls = win_status_cls(status, due)
        rows += f"""<div class="ev-window">
  <span class="ev-status {scls}">{scls.replace("-"," ")}</span>
  <div class="ev-window-body">
    <div class="ev-window-name">{name}</div>
    {"<div class='ev-controls'>" + controls + "</div>" if controls else ""}
    <div class="ev-meta">{"Due: " + e(due) if due else ""}{" · Owner: " + owner if owner else ""}</div>
  </div>
</div>"""

    overdue_count = sum(
        1 for w in windows if isinstance(w, dict)
        and win_status_cls(str(w.get("status","")), str(w.get("due_date",""))) == "overdue"
    )
    badge_cls = " warn" if overdue_count else ""
    badge_txt = f"{len(windows)} window{'s' if len(windows)!=1 else ''}"
    if overdue_count:
        badge_txt += f" · {overdue_count} overdue"

    return f"""<div class="card">
  <div class="card-header">
    <div class="card-title">Evidence Collection Windows</div>
    <div class="card-badge{badge_cls}">{badge_txt}</div>
  </div>
  <div class="card-body">{rows}</div>
</div>"""


# ---------------------------------------------------------------------------
# Top-level HTML assembly
# ---------------------------------------------------------------------------

def generate_html(run: dict) -> str:
    today = date.today().isoformat()
    name = get_program_name(run)
    frameworks = get_frameworks(run)
    health = get_health(run)

    # Core sections
    header = render_header(run)
    staleness = render_staleness_notice(run)
    status_bar = render_status_bar(run)
    priorities = render_priorities_banner(run)
    escalations = render_escalations(run)
    stats = render_stats_row(run)

    # New rich sections
    scope_card = render_scope_card(run)
    stakeholders = render_stakeholder_grid(run)
    commitments = render_commitments(run)
    evidence_windows = render_evidence_windows(run)

    # Existing sections
    coverage = render_coverage_section(run)
    risk = render_risk_register(run)
    decisions = render_decision_queue(run)
    watch = render_watch_list(run)
    calendar_html = render_calendar(run)
    vendor = render_vendor_scorecard(run)
    flags = render_flags(run)
    next_run = render_next_run(run)

    # Row: scope + stakeholders (side by side if both present)
    scope_row = ""
    if scope_card or stakeholders:
        if scope_card and stakeholders:
            scope_row = f'<div class="grid-2" style="margin-bottom:20px;">{scope_card}{stakeholders}</div>'
        else:
            scope_row = f'<div style="margin-bottom:20px;">{scope_card or stakeholders}</div>'

    # Row: risk + decisions
    risk_row = ""
    if risk or decisions:
        if risk and decisions:
            risk_row = f'<div class="grid-2" style="margin-bottom:20px;">{risk}{decisions}</div>'
        else:
            risk_row = f'<div style="margin-bottom:20px;">{risk or decisions}</div>'

    # Row: evidence windows + calendar events (evidence windows primary; calendar secondary)
    cal_row = ""
    if evidence_windows or calendar_html or watch:
        if evidence_windows and (calendar_html or watch):
            right = calendar_html or watch
            cal_row = f'<div class="grid-2" style="margin-bottom:20px;">{evidence_windows}{right}</div>'
        elif evidence_windows:
            cal_row = f'<div style="margin-bottom:20px;">{evidence_windows}</div>'
        elif watch and calendar_html:
            cal_row = f'<div class="grid-2" style="margin-bottom:20px;">{watch}{calendar_html}</div>'
        else:
            cal_row = f'<div style="margin-bottom:20px;">{watch or calendar_html}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(name)} — Compliance Dashboard — {today}</title>
<style>{CSS}</style>
</head>
<body>

{header}

<div class="main">

{staleness}
{status_bar}
{priorities}
{escalations}
{stats}
{scope_row}
{coverage}
{risk_row}
{commitments}
{cal_row}
{vendor}
{flags}
{next_run}

</div>
<footer>Generated by program-pipeline · {today} · Governed by config/constitution.md</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def load_run(runs_dir: Path, slug: str) -> dict:
    path = runs_dir / slug / "latest.json"
    if not path.exists():
        print(f"ERROR: No latest.json found for program '{slug}' at {path}",
              file=sys.stderr)
        sys.exit(1)
    with path.open(encoding="utf-8") as f:
        run = json.load(f)
    run["_program_slug"] = slug
    return run


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a 62443-style light-theme per-program dashboard."
    )
    parser.add_argument("--program", required=True,
                        help="Program slug (must match a runs/[slug]/ directory)")
    parser.add_argument("--runs", default="runs",
                        help="Path to the runs directory (default: ./runs)")
    parser.add_argument("--output", default=None,
                        help="Output HTML path (default: runs/[slug]/dashboard.html)")
    args = parser.parse_args()

    runs_dir = Path(args.runs)
    run = load_run(runs_dir, args.program)

    out_path = Path(args.output) if args.output else runs_dir / args.program / "dashboard.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    html = generate_html(run)
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to: {out_path}")
    print(f"  Program: {get_program_name(run)}")
    print(f"  Health:  {get_health(run)}")
    print(f"  Schema:  {get_schema(run)}")


if __name__ == "__main__":
    main()
