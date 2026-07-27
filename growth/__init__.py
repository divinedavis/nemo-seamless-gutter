"""NEMO Seamless Gutter growth engine.

A self-improving daily loop: measure yesterday, judge what's running, retire what
isn't working, scout for new techniques, build and deploy the ones that are
approved, then report.

The ledger (techniques.json) — not this code — decides what runs each morning,
so a technique can be switched off without a deploy.
"""
