import json
from typing import List, Dict, Any, Tuple
import operator
import streamlit as st

#rule engine 
OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}

# default scholarship rules 
DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0]
        ],
        "action": {
            "decision": "AWARD_FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need"
        }
    },
    {
        "name": "Good candidate - partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1]
        ],
        "action": {
            "decision": "AWARD_PARTIAL",
            "reason": "Good academic & involvement record with moderate need"
        }
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000]
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score"
        }
    },
    {
        "name": "Low CGPA – not eligible",
        "priority": 95,
        "conditions": [
            ["cgpa", "<", 2.5]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement"
        }
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [
            ["disciplinary_actions", ">=", 2]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records"
        }
    }
]

def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    """Evaluate one condition [field, operator, value]."""
    if len(cond) != 3:
        return False
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False
    try:
        return OPS[op](facts[field], value)
    except Exception:
        return False

def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))

def run_rules(
    facts: Dict[str, Any],
    rules: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:

    fired = [r for r in rules if rule_matches(facts, r)]

    if not fired:
        return {"decision": "NO_RULE", "reason": "No rules matched"}, []

    fired_sorted = sorted(fired, key=lambda r: r.get("priority", 0), reverse=True)
    best_rule = fired_sorted[0].get("action", {"decision": "NO_ACTION", "reason": "-"})

    return best_rule, fired_sorted

# streamlit ui 
st.set_page_config(page_title="Scholarship Rule-Based System", layout="wide")
st.title("Scholarship Eligibility – Rule-Based System")
st.caption("Transparent, rule-driven scholarship advisory system using JSON rules.")

with st.sidebar:
    st.header("Applicant Information")

    cgpa = st.number_input("CGPA", min_value=0.0, max_value=4.0, step=0.01, value=3.0)
    family_income = st.number_input("Family income (MYR)", min_value=0, step=100, value=5000)
    co_score = st.number_input("Co-curricular score (0–100)", min_value=0, max_value=100, value=70)
    semester = st.number_input("Current semester", min_value=1, max_value=12, value=4)
    disciplinary = st.number_input("Disciplinary actions", min_value=0, value=0)

    st.divider()
    st.header("Rules (JSON Editor)")

    rules_text = st.text_area(
        "Edit rules here",
        value=json.dumps(DEFAULT_RULES, indent=2),
        height=300
    )

    run = st.button("Evaluate", type="primary")

facts = {
    "cgpa": float(cgpa),
    "family_income": int(family_income),
    "co_curricular_score": int(co_score),
    "semester": int(semester),
    "disciplinary_actions": int(disciplinary)
}

st.subheader("Applicant Facts")
st.json(facts)

try:
    rules = json.loads(rules_text)
    assert isinstance(rules, list), "Rules must be an array."
except Exception as e:
    st.error(f"Invalid JSON! Reverting to default rules. Details: {e}")
    rules = DEFAULT_RULES

st.subheader("Active Rules")
with st.expander("View Rules JSON", expanded=False):
    st.code(json.dumps(rules, indent=2), language="json")

st.divider()

if run:
    action, fired = run_rules(facts, rules)

    col1, col2 = st.columns([1, 1])

    
    with col1:
        st.subheader("Final Decision")
        dec = action.get("decision", "REVIEW")
        reason = action.get("reason", "-")

        if dec == "AWARD_FULL":
            st.success(f"FULL SCHOLARSHIP — {reason}")
        elif dec == "AWARD_PARTIAL":
            st.success(f"PARTIAL SCHOLARSHIP — {reason}")
        elif dec == "REJECT":
            st.error(f"REJECTED — {reason}")
        elif dec == "REVIEW":
            st.warning(f"REVIEW REQUIRED — {reason}")
        else:
            st.info(dec)

    
    with col2:
        st.subheader("Matched Rules (By Priority)")
        if not fired:
            st.info("No rules matched the applicant.")
        else:
            for i, rule in enumerate(fired, start=1):
                st.write(f"**{i}. {rule.get('name')}** | priority={rule.get('priority')}")
                st.caption(f"Action: {rule.get('action')}")
                with st.expander("Conditions"):
                    for cond in rule.get("conditions", []):
                        st.code(str(cond))

else:
    st.info("Enter applicant data and click **Evaluate** to run the rule engine.")
