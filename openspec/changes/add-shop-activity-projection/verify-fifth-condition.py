"""Exercise verify.sh's fifth condition, extracted verbatim from the script.

The block is read out of `deploy/demo/verify.sh` rather than retyped here, so this cannot
drift from what actually runs: if somebody edits the script, this exercises the edit.
"""

import pathlib
import re
import sys

VERIFY = pathlib.Path(sys.argv[1])
source = VERIFY.read_text(encoding="utf-8")

# The fifth-condition block: from the projection lookup to the start of the sixth condition.
match = re.search(
    r"^projection = body\.get\(\"projection\"\).*?(?=^# Sixth condition)",
    source,
    re.S | re.M,
)
assert match, "could not locate the fifth condition block in verify.sh"
BLOCK = match.group(0)

# And the wait helper, so the version-skew tolerance is exercised too.
wait_match = re.search(r"^def drains_have_run\(payload\):.*?(?=^deadline = )", source, re.S | re.M)
assert wait_match, "could not locate drains_have_run in verify.sh"
WAIT = wait_match.group(0)


def evaluate(body):
    scope = {"body": body, "failures": []}
    exec(BLOCK, scope)
    return scope["failures"]


def drains_have_run(payload):
    scope = {}
    exec(WAIT, scope)
    return scope["drains_have_run"](payload)


def projection(**overrides):
    base = {
        "status": "ok",
        "age_seconds": 12.0,
        "points_of_sale": 12,
        "active_points_of_sale": 11,
        "shops_without_scope": 0,
    }
    base.update(overrides)
    return {"projection": base}


CASES = []


def case(name, body, expect_failure, expect_contains=None):
    CASES.append((name, body, expect_failure, expect_contains))


# --- the finding this change exists for -------------------------------------------------
case(
    "a shop closed on purpose PASSES (the 2026-09-27 false positive)",
    projection(points_of_sale=12, active_points_of_sale=11, shops_without_scope=0),
    expect_failure=False,
)
case(
    "an ACTIVE shop without assortment still FAILS",
    projection(points_of_sale=12, active_points_of_sale=12, shops_without_scope=1),
    expect_failure=True,
    expect_contains="ACTIVE point(s) of sale hold no assigned row",
)

# --- the empty-table case, which must not pass in a vacuum ------------------------------
case(
    "ai.pos_shop empty FAILS rather than passing vacuously",
    projection(points_of_sale=12, active_points_of_sale=0, shops_without_scope=None),
    expect_failure=True,
    expect_contains="knows of no active point of sale",
)
case(
    "an unreadable projection section FAILS",
    projection(
        status="unavailable",
        points_of_sale=None,
        active_points_of_sale=None,
        shops_without_scope=None,
    ),
    expect_failure=True,
    expect_contains="could not read how many points of sale are active",
)

# --- what the old conditions already caught, unchanged ----------------------------------
case(
    "a projection never drained FAILS",
    projection(status="never_drained", points_of_sale=0, active_points_of_sale=0),
    expect_failure=True,
    expect_contains="never been drained",
)
case(
    "an empty projection FAILS",
    projection(points_of_sale=0, active_points_of_sale=11, shops_without_scope=11),
    expect_failure=True,
    expect_contains="holds no rows at all",
)

# --- version skew: an older AI image -----------------------------------------------------
case(
    "an image predating C43 (no active_points_of_sale) does NOT fail",
    {
        "projection": {
            "status": "ok",
            "age_seconds": 12.0,
            "points_of_sale": 12,
            "shops_without_scope": 0,
        }
    },
    expect_failure=False,
)
case(
    "an image predating C41 (no projection section at all) does NOT fail",
    {},
    expect_failure=False,
)

failed = 0
for name, body, expect_failure, expect_contains in CASES:
    failures = evaluate(body)
    got = bool(failures)
    ok = got == expect_failure
    if ok and expect_contains:
        ok = any(expect_contains in f for f in failures)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"        expected failure={expect_failure} contains={expect_contains!r}")
        print(f"        got {failures}")
        failed += 1

print()
print("  drains_have_run:")
WAIT_CASES = [
    ("drained, eleven active -> do not wait", projection()["projection"], True),
    ("never_drained -> wait", projection(status="never_drained")["projection"], False),
    ("zero active -> wait", projection(active_points_of_sale=0)["projection"], False),
    (
        "image predating C43 -> do not wait (nothing to wait for)",
        {"status": "ok", "points_of_sale": 12, "shops_without_scope": 0},
        True,
    ),
    ("no projection section -> do not wait", None, True),
]
for name, payload, expected in WAIT_CASES:
    got = drains_have_run({"projection": payload} if payload is not None else {})
    ok = got == expected
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"        expected {expected}, got {got}")
        failed += 1

print()
print(f"{'ALL GREEN' if not failed else str(failed) + ' FAILED'}")
sys.exit(1 if failed else 0)
