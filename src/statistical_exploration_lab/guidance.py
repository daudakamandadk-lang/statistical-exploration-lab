"""Explicit, deterministic guidance from selected descriptive evidence.

No tests, model selection, confidence ratings or statistical estimation here.
The caller supplies the question and why this calculation is relevant.
"""
from copy import copy
from .grouped import GroupedProportions
from .exploration import Exploration
from .investigation_report import InvestigationSection, _result_digest


def explain_result(result, *, question, relevance):
    """Snapshot a grouped/relationship result and explain its actual status.

    Facts are formatted from supplied statistics; next checks are transparent
    rules, not executed investigations. The caller retains the choice of method,
    field roles, population and any follow-up. No source data is modified.
    """
    if not all(isinstance(t, str) and t.strip() for t in (question, relevance)):
        raise ValueError('Supply a question and the relevance of the selected calculation')
    if not isinstance(result, (GroupedProportions, Exploration)):
        raise TypeError('Supply a grouped binary or relationship result')
    # A result's editable tables must not silently change an existing explanation.
    saved = copy(result)
    object.__setattr__(saved, 'table', result.table.copy(deep=True))
    if isinstance(result, Exploration):
        object.__setattr__(saved, 'rows', result.rows.copy(deep=True))
    facts, next_checks = [], []
    if isinstance(saved, GroupedProportions):
        weighted = saved.choices['weight'] is not None
        label = 'weighted' if weighted else 'unweighted'
        for row in saved.table.itertuples(index=False):
            group = str(row.group)
            counts = (f'{int(row.events)} recorded events / {int(row.used)} usable observations; '
                      f'{int(row.missing_outcome)} missing eligible outcomes; {int(row.ineligible)} ineligible')
            if row.status == 'not_estimable':
                facts.append(f'{group}: percentage unavailable ({counts}).')
                next_checks.append(f'{group}: review eligibility and missing outcomes before comparing percentages; there is no usable denominator.')
            else:
                facts.append(f'{group}: {100*row.proportion:.1f}% {label} ({counts}).')
                if row.missing_outcome:
                    next_checks.append(f'{group}: inspect the {int(row.missing_outcome)} missing eligible outcomes and whether their exclusion changes the comparison.')
        if not len(saved.table):
            facts.append('No observed groups are available.')
            next_checks.append('Review the input selection; there are no groups to compare.')
        if not next_checks:
            next_checks.append('No eligible outcomes were excluded for missingness. Confirm category meanings and population coverage before choosing a substantive subgroup comparison.')
        if weighted:
            next_checks.append('Identify what the weights represent and the sampling design before adding population uncertainty intervals.')
        meaning = ('These percentages describe the explicitly coded event in the supplied groups. '
                   'Counts are unweighted; weighted percentages need not equal events divided by usable observations. '
                   if weighted else 'These percentages describe the explicitly coded event among usable observations in each supplied group. ')
        meaning += 'A group difference alone does not explain its cause or justify a model choice.'
        purpose = 'Percent describes event frequency; events, usable observations, missing outcomes and eligibility expose the denominator.'
        limits = 'No uncertainty interval, significance test, adjustment for other variables or population representativeness assessment has been calculated.'
    elif 'coefficient' in saved.table:
        method = saved.choices['method'].title()
        for row in saved.table.itertuples(index=False):
            pair = f'{row.left} / {row.right}'
            if row.status not in ('estimated', 'estimated_with_warning'):
                facts.append(f'{pair}: {method} correlation unavailable ({row.status}); {int(row.used)} usable pairs, {int(row.excluded)} excluded.')
                reason = ('at least one field is constant in the paired sample; verify the selected field and filter'
                          if row.status == 'constant_input' else
                          'fewer than three complete pairs remain; inspect missingness and obtain more suitable observations'
                          if row.status == 'insufficient_pairs' else
                          'the numerical calculation was unavailable; inspect the scales and recorded warnings')
                next_checks.append(f'{pair}: {reason}.')
            else:
                facts.append(f'{pair}: {method} correlation {row.coefficient:.3f}; {int(row.used)} usable pairs, {int(row.excluded)} excluded.')
                if row.excluded:
                    next_checks.append(f'{pair}: inspect the {int(row.excluded)} excluded pairs before comparing this coefficient with another sample.')
                if row.warnings:
                    next_checks.append(f'{pair}: review the numerical warning: {row.warnings}')
                next_checks.append(f'{pair}: inspect a scatterplot on these same usable pairs for curves, clusters and influential observations before proposing a relationship form.')
        if not len(saved.table):
            facts.append('No selected relationships are available.')
            next_checks.append('Select a pair relevant to the question before investigating association.')
        meaning = (f'{method} describes ' + ('linear association' if method == 'Pearson' else 'monotonic rank association') +
                   '. A coefficient near zero does not establish independence or absence of other patterns. An unavailable coefficient is not zero.')
        purpose = 'The coefficient describes the selected association; usable/excluded pair counts and status identify which evidence supports it.'
        limits = 'Unweighted descriptive association only. No causal claim, significance test, predictive validation or model selection. Plot inspection is suggested, not performed by this helper.'
    else:
        raise TypeError('Automatic guidance currently supports grouped binary and relationship results only')
    return InvestigationSection(
        question=question, result=saved, observation=' '.join(facts),
        interpretation=meaning, next_step=' '.join(dict.fromkeys(next_checks)),
        limitations=limits, metric_purpose=f'{relevance} {purpose}',
        explanation_source='rule-based descriptive guidance', evidence_digest=_result_digest(saved))
