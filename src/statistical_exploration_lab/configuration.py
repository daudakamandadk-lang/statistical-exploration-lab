"""A deliberately small, strict configuration contract for the first learning build."""

import json
from pathlib import Path


def _object(value, required, location):
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be an object")
    unknown = set(value) - set(required)
    missing = set(required) - set(value)
    if unknown or missing:
        raise ValueError(f"{location}: missing={sorted(missing)}, unknown={sorted(unknown)}")


def _text(value, location):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location} must be nonblank text")


def _names(value, location, allow_empty=True):
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ValueError(f"{location} must be a {'nonempty ' if not allow_empty else ''}list")
    for name in value:
        _text(name, location)
    if len(value) != len(set(value)):
        raise ValueError(f"{location} contains duplicate names")


def validate_configuration(config):
    """Reject unimplemented settings rather than silently ignoring them."""
    _object(config, ['version', 'question', 'input', 'observation', 'fields',
                     'minimum_samples', 'relationships'], 'configuration')
    if type(config['version']) is not int or config['version'] != 1:
        raise ValueError('Only configuration version 1 is supported')
    _text(config['question'], 'question')
    _object(config['input'], ['path'], 'input')
    _text(config['input']['path'], 'input.path')
    _object(config['observation'], ['grain', 'unit', 'key'], 'observation')
    for name in ('grain', 'unit'):
        _text(config['observation'][name], f'observation.{name}')
    _names(config['observation']['key'], 'observation.key', allow_empty=False)
    _object(config['fields'], ['identifiers', 'numeric', 'categorical', 'excluded'], 'fields')
    all_fields = []
    for role, names in config['fields'].items():
        _names(names, f'fields.{role}')
        all_fields.extend(names)
    if len(all_fields) != len(set(all_fields)):
        raise ValueError('Each field must have exactly one declared role')
    if not set(config['observation']['key']) <= set(config['fields']['identifiers']):
        raise ValueError('Every observation key must be declared as an identifier')
    _object(config['minimum_samples'], ['numeric_pair', 'categorical_pair', 'group'],
            'minimum_samples')
    for name, value in config['minimum_samples'].items():
        smallest = 2 if name == 'numeric_pair' else 1
        if type(value) is not int or value < smallest:
            raise ValueError(f'minimum_samples.{name} must be an integer >= {smallest}')
    relationships = config['relationships']
    _object(relationships, ['numeric_pairs', 'numeric_methods', 'categorical_pairs',
                            'group_summaries'], 'relationships')
    _names(relationships['numeric_methods'], 'numeric_methods', allow_empty=False)
    if not set(relationships['numeric_methods']) <= {'pearson', 'spearman'}:
        raise ValueError('numeric_methods supports pearson and spearman only')
    for kind in ('numeric', 'categorical'):
        pairs = relationships[f'{kind}_pairs']
        if not isinstance(pairs, list):
            raise ValueError(f'{kind}_pairs must be a list')
        seen = set()
        for pair in pairs:
            _names(pair, f'{kind}_pair', allow_empty=False)
            if len(pair) != 2 or not set(pair) <= set(config['fields'][kind]):
                raise ValueError(f'{kind}_pairs requires two distinct {kind} fields')
            identity = frozenset(pair)
            if identity in seen:
                raise ValueError(f'Duplicate {kind} pair')
            seen.add(identity)
    groups = relationships['group_summaries']
    if not isinstance(groups, list):
        raise ValueError('group_summaries must be a list')
    seen_groups = set()
    for group in groups:
        _object(group, ['group_by', 'measure'], 'group_summary')
        if (group['group_by'] not in config['fields']['categorical']
                or group['measure'] not in config['fields']['numeric']):
            raise ValueError('group summaries require a categorical group and numeric measure')
        identity = (group['group_by'], group['measure'])
        if identity in seen_groups:
            raise ValueError('Duplicate group summary')
        seen_groups.add(identity)
    return config


def _unique_keys(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f'Duplicate JSON setting: {key}')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f'Nonfinite JSON value: {value}')


def load_configuration(path):
    with Path(path).open(encoding='utf-8-sig') as handle:
        config = json.load(handle, object_pairs_hook=_unique_keys,
                           parse_constant=_reject_constant)
    return validate_configuration(config)
