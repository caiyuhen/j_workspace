from __future__ import annotations


class TL:
    LOW = 'low'
    SOME = 'some_concerns'
    HIGH = 'high'
    CRIT = 'critical'
    NI = 'ni'


def r(d, rating):
    return {'domain': f'D{d}', 'rating': rating}


def calc_rob2_overall(domains):
    rs = [item['rating'] for item in domains]
    if TL.HIGH in rs:
        return TL.HIGH
    some_count = sum(1 for x in rs if x == TL.SOME)
    if some_count >= 2:
        return TL.SOME
    if some_count == 1:
        return TL.SOME
    return TL.LOW


def calc_robinsi_overall(domains):
    rs = [item['rating'] for item in domains]
    if TL.CRIT in rs:
        return TL.CRIT
    if TL.HIGH in rs:
        return TL.HIGH
    some_count = sum(1 for x in rs if x == TL.SOME)
    if some_count >= 1:
        return TL.SOME
    return TL.LOW


def domain_d1_rating(signals):
    open_label = signals.get('open_label', False)
    outcome_type = signals.get('outcome_type', None)
    blinded_outcome = signals.get('blinded_outcome', True)
    if open_label and outcome_type == 'subjective' and not blinded_outcome:
        return TL.HIGH
    if open_label and outcome_type == 'objective':
        return TL.SOME
    return TL.LOW


def grade_ro_downgrade(study_ratings):
    n = len(study_ratings)
    if n == 0:
        return 0
    crit_count = sum(1 for x in study_ratings if x == TL.CRIT)
    high_count = sum(1 for x in study_ratings if x == TL.HIGH)
    some_count = sum(1 for x in study_ratings if x == TL.SOME)
    if crit_count > 0:
        return -2
    high_pct = high_count / n
    some_pct = some_count / n
    if high_pct >= 0.5:
        return -2
    if high_pct >= 0.25 or some_pct >= 0.25:
        return -1
    return 0
