from crp.llm.evaluate import compile_rule, evaluate_rule
from crp.llm.prompts import FUNCTION_DESCRIPTION, TEMPLATE_PROGRAM
from test_llm_evaluate import RETURN_SH_TRAIN


def test_template_runs_and_scores_like_return_sh(training_set):
    func = compile_rule(TEMPLATE_PROGRAM, "priority")
    assert evaluate_rule(func, training_set, 0.5) == RETURN_SH_TRAIN


def test_function_description_names_every_input():
    for name in ("SH", "EMP", "AVG", "CUR", "RI", "DIFF"):
        assert f"{name} = " in FUNCTION_DESCRIPTION
