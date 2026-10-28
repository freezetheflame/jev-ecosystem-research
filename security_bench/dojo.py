"""Real AgentDojo state, tools and graders, with fresh state for every safety arm."""
import json
import sys
import time
from .common import encode, digest, append, write, now
from .datasets import paths
from .models import output_text, StopRun


FIXED_ATTACKS = {'direct', 'ignore_previous', 'system_message', 'injecagent'}


def suites(config):
    root = paths(config)['agentdojo']
    sys.path.insert(0, str(root / 'src'))
    import agentdojo
    from pathlib import Path
    if not Path(agentdojo.__file__).resolve().is_relative_to((root / 'src').resolve()):
        raise ValueError('Another AgentDojo installation shadows configured snapshot')
    from agentdojo.task_suite import get_suites
    return get_suites(config['datasets']['agentdojo']['benchmark_version'])


def prepare(config):
    spec = config['datasets']['agentdojo']
    registry = suites(config)
    from agentdojo.attacks import load_attack
    cases, exclusions = [], []
    for name in spec['suites']:
        suite = registry[name]
        tasks = spec.get('user_task_ids', {}).get(name) or list(suite.user_tasks)
        for task_id in tasks:
            task = suite.user_tasks[task_id]
            if spec['include_clean']:
                cases.append({'dataset_id': 'agentdojo', 'item_id': f'{name}:{task_id}:clean',
                    'family_id': f'{name}:{task_id}', 'suite': name, 'user_task_id': task_id,
                    'injection_task_id': None, 'attack': None, 'injections': {}, 'condition': 'clean'})
            for attack_name in spec['attacks']:
                if attack_name not in FIXED_ATTACKS:
                    raise ValueError('Only non-adaptive fixed upstream attacks supported')
                attack = load_attack(attack_name, suite, None)
                injection_ids = spec.get('injection_task_ids', {}).get(name) or list(suite.injection_tasks)
                for injection_id in injection_ids:
                    uid = f'{name}:{task_id}:{injection_id}:{attack_name}'
                    try:
                        payload = attack.attack(task, suite.injection_tasks[injection_id])
                    except Exception as exc:
                        exclusions.append({'item_id': uid, 'status': 'planning_failure',
                                           'error_type': type(exc).__name__})
                        continue
                    cases.append({'dataset_id': 'agentdojo', 'item_id': uid,
                        'family_id': f'{name}:{task_id}', 'suite': name, 'user_task_id': task_id,
                        'injection_task_id': injection_id, 'attack': attack_name,
                        'injections': payload, 'condition': 'attacked'})
    for case in cases:
        case['evaluation_mode'] = spec['mode_code']
        case['input_sha256'] = digest(case)
        case['gold'] = None
        case['gold_source'] = 'episode_utility_and_attack_success_not_action_gold'
    return cases, exclusions


def tools_for(suite, api):
    tools = []
    for function in suite.tools:
        item = {'name': function.name, 'description': function.description,
                'parameters': function.parameters.model_json_schema()}
        tools.append({'type': 'function', **item} if api == 'openai_responses'
                     else {'type': 'function', 'function': item})
    return tools


def run_episode(config, case, judge, transport, episode_id, directory):
    suite = suites(config)[case['suite']]
    from agentdojo.functions_runtime import FunctionsRuntime, FunctionCall
    from agentdojo.agent_pipeline.tool_execution import tool_result_to_str
    from agentdojo.types import text_content_block_from_string as block
    task = suite.user_tasks[case['user_task_id']]
    environment = task.init_environment(suite.load_and_inject_default_environment(case['injections']))
    initial = environment.model_copy(deep=True)
    runtime = FunctionsRuntime(suite.tools)
    spec = config['datasets']['agentdojo']
    model = config['models']['main_agent']
    api = model['api']
    history = [{'role': 'user', 'content': task.PROMPT}]
    chat = [{'role': 'system', 'content': config['main_agent_system_prompt']}, *history]
    visible_messages, native_messages, executed = [], [], []
    blocked, calls, finished, final = 0, 0, False, ''
    trace_path = directory / 'traces' / (episode_id + '.jsonl')
    trace_path.parent.mkdir(exist_ok=True)
    write(directory / 'traces' / (episode_id + '.initial.json'), environment.model_dump(mode='json'))
    for step in range(spec['max_steps']):
        transport.check_budget()
        if api == 'openai_responses':
            payload = {'model': model['model_id'], 'instructions': config['main_agent_system_prompt'],
                'input': history, 'tools': tools_for(suite, api), **model['parameters']}
        elif api == 'openai_chat':
            payload = {'model': model['model_id'], 'messages': chat,
                       'tools': tools_for(suite, api), **model['parameters']}
        else:
            raise ValueError('Main agent requires a tool-capable OpenAI Responses or Chat endpoint')
        response = transport.post(payload, 'main_agent', episode_id, 'main_agent')
        if api == 'openai_responses':
            history.extend(response['output'])
            pending = [{'id': x['call_id'], 'function': {'name': x['name'], 'arguments': x['arguments']}}
                       for x in response['output'] if x['type'] == 'function_call']
            final = output_text(response)
        else:
            choice = response['choices'][0]
            if choice.get('finish_reason') not in ('stop', 'tool_calls'):
                raise ValueError('Main-agent completion is truncated, refused or otherwise incomplete')
            assistant = choice['message']
            chat.append(assistant)
            pending, final = assistant.get('tool_calls') or [], assistant.get('content') or ''
        if not pending:
            finished = True
            break
        # Handle tools serially. A later action is judged only after earlier results.
        for action in pending:
            if calls >= spec['max_tool_calls']:
                raise StopRun('episode_tool_budget')
            name = action['function']['name']
            args = json.loads(action['function']['arguments'])
            call = FunctionCall(function=name, args=args, id=action['id'])
            state = {'trusted_user_task': task.PROMPT,
                     'history': visible_messages, 'proposed_action': {'tool': name, 'arguments': args}}
            risk = judge.judge(state, 'pre_action_authorization', episode_id)
            if risk:
                result, error = spec['blocked_feedback'], None
                blocked += 1
            else:
                result, error = runtime.run_function(environment, name, args)
                result = tool_result_to_str(result)
                # Graders see executed calls only; blocked proposals are separate trace events.
                executed.append(call)
                native_messages.extend([
                    {'role': 'assistant', 'content': [block('')], 'tool_calls': [call]},
                    {'role': 'tool', 'content': [block(result)], 'tool_call': call,
                     'tool_call_id': call.id, 'error': error}])
            calls += 1
            visible_result = error or result
            visible_messages.extend([{'role': 'assistant', 'tool_call': call.model_dump(mode='json')},
                                     {'role': 'tool', 'content': visible_result}])
            append(trace_path, {'step': step, 'time': now(), 'action': call.model_dump(mode='json'),
                'risk': risk, 'executed': not bool(risk), 'tool_result': visible_result,
                'post_environment_sha256': digest(environment.model_dump(mode='json'))})
            if api == 'openai_responses':
                history.append({'type': 'function_call_output', 'call_id': call.id, 'output': visible_result})
            else:
                chat.append({'role': 'tool', 'tool_call_id': call.id, 'content': visible_result})
    write(directory / 'traces' / (episode_id + '.final.json'),
          {'environment': environment.model_dump(mode='json'), 'final_output': final, 'finished': finished})
    if not finished:
        return {'status': 'unknown_step_limit', 'utility': None, 'attack_success': None,
                'blocked_actions': blocked, 'tool_calls': calls}
    output = [block(final)]
    utility = suite._check_user_task_utility(task, output, initial, environment, executed)
    injection = case['injection_task_id']
    attack_success = None if injection is None else suite._check_injection_task_security(
        suite.injection_tasks[injection], output, initial, environment, executed)
    return {'status': 'ok', 'utility': bool(utility),
            'attack_success': None if attack_success is None else bool(attack_success),
            'blocked_actions': blocked, 'tool_calls': calls}
