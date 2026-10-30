from adapters.base import Work
from matching import evaluate, normalize
from models import ReferenceInput

TITLE = "Deep Learning for Bathroom Accessibility"


def ref(**overrides) -> ReferenceInput:
    data = {"title": TITLE, "authors": ["Müller"], "year": 2020}
    data.update(overrides)
    return ReferenceInput(**data)


def work(**overrides) -> Work:
    data = {"title": TITLE, "year": 2020, "authors": ["Anna Müller"], "source": "Test"}
    data.update(overrides)
    return Work(**data)


def test_normalize_removes_accents_and_punctuation():
    assert normalize("Äpfel: Müller!") == "apfel muller"


def test_exact_match_is_gefunden():
    assert evaluate(ref(), [work()]).status == "gefunden"


def test_wrong_year_is_abweichend():
    verdict = evaluate(ref(), [work(year=2014)])
    assert verdict.status == "abweichend"
    assert any("Jahr" in issue for issue in verdict.issues)


def test_year_within_tolerance_is_still_gefunden():
    assert evaluate(ref(), [work(year=2021)]).status == "gefunden"


def test_wrong_author_is_abweichend():
    verdict = evaluate(ref(), [work(authors=["Anna Schmidt"])])
    assert verdict.status == "abweichend"
    assert any("Autoren" in issue for issue in verdict.issues)


def test_missing_author_data_is_not_a_mismatch():
    assert evaluate(ref(), [work(authors=[])]).status == "gefunden"


def test_unrelated_title_is_nicht_gefunden():
    other = work(title="Quantum chromodynamics on the lattice")
    assert evaluate(ref(), [other]).status == "nicht gefunden"


def test_similar_title_is_unsicher():
    similar = work(title="Deep Learning for Bathroom Accessibility Analysis")
    assert evaluate(ref(), [similar]).status == "unsicher"


def test_empty_results_are_nicht_gefunden():
    assert evaluate(ref(), []).status == "nicht gefunden"


def test_doi_match_beats_title_difference():
    doi_work = work(title="Completely different wording", doi="10.1234/abc", authors=[], year=None)
    verdict = evaluate(ref(doi="https://doi.org/10.1234/ABC"), [doi_work])
    assert verdict.status == "gefunden"
