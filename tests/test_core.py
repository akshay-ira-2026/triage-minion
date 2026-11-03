from triage_minion.core import Issue, classify, severity, score, triage, to_markdown

def I(n, t, b="", c=0, l=None, age=0): return Issue(n, t, b, c, l or [], age, f"https://x/{n}")

def test_bug_detected():
    assert classify(I(1, "App crashes on start"))[0] == "bug"

def test_security_is_critical():
    i = I(2, "Token leak in logs"); k, _ = classify(i)
    assert k == "security" and severity(i, k) == "critical"

def test_existing_label_wins():
    assert classify(I(3, "crash", l=["documentation"]))[0] == "docs"

def test_regression_high():
    i = I(4, "Regression: login broken after 2.1"); assert severity(i, classify(i)[0]) in ("high", "critical")

def test_ordering_by_score():
    rows = triage([I(5, "typo in README"), I(6, "crash with data loss", c=8, age=30)])
    assert rows[0].number == 6

def test_score_caps():
    assert score(I(7, "x", c=999, age=999), "low") == 4 + 30 + 10

def test_markdown():
    md = to_markdown("o/r", triage([I(8, "Add dark mode")]))
    assert "#8 Add dark mode" in md and "kind: feature" in md
