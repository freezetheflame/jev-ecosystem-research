"""Versioned retry contract and conservative budget reservations; no fee estimation."""
import math

POLICY = {'max_attempts': 5, 'base_delay_seconds': 2, 'max_delay_seconds': 60,
          'http_statuses': [408, 409, 425, 429, 500, 502, 503, 504],
          'network': True, 'decode': True, 'format': True, 'refusal': True,
          'selection': 'first_valid_prediction'}


def validate(policy):
    if not isinstance(policy, dict) or set(policy) != set(POLICY):
        return False
    return (type(policy['max_attempts']) is int and 1 <= policy['max_attempts'] <= 10
            and all(type(policy[k]) in (int, float) and math.isfinite(policy[k]) and policy[k] >= 0
                    for k in ('base_delay_seconds', 'max_delay_seconds'))
            and policy['base_delay_seconds'] <= policy['max_delay_seconds'] <= 60
            and policy['http_statuses'] == POLICY['http_statuses']
            and all(type(policy[k]) is bool for k in ('network', 'decode', 'format', 'refusal'))
            and policy['selection'] == 'first_valid_prediction')


def unknown_calls(events):
    return sum(e.get('provider') != 'local' and e.get('estimated_cost_usd') is None
               and e.get('error_type') != 'PolicyRefusal' for e in events)


def reservation(config, events):
    # A scheduling allowance, never a replacement for null actual/estimated fees.
    return unknown_calls(events) * config['budget']['reserve_usd_per_call']
