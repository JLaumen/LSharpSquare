from algorithm import learn
from fa_learner import FALearner
from dfa3_encoder import DFA3Encoder
from rpni_learner import RPNILearner
from aalpy.utils import make_input_complete, load_automaton_from_file
from rc_lstar import run_Lstar
import time
from system_dc_sul_s_t import SystemDCSULST
from system_dc_oracle_s_t import SystemDCOracleST
from complete_dfa_oracle import CompleteDFAOracle
from copy import deepcopy
from aalpy.base.SUL import CacheSUL
from rers_sul_s_t import RERSSULST
from data.counter_examples import counter_examples_dict
from multiprocessing import Process, Queue
import random
from RandomWalkEquOracly import RandomWalkEqOracle
from WMethodEqOracle import RandomWMethodEqOracle
from LSharpSquare import run_lsharp_square
from RandomWordEqOracle import RandomWordEqOracle


def run(example, t_type):
    # T2 update
    M = load_automaton_from_file(f'data/{example}/T{t_type}.dot', automaton_type='dfa') #
    make_input_complete(M, missing_transition_go_to="sink_state")

    # # T2 update
    # from symbolic_dfa_t2 import SymbolicDFAT2
    # M = SymbolicDFAT2(counter_examples_dict[example][t_type][0][1])

    system_sul = CacheSUL(
        RERSSULST(benchmark=example, t_type=t_type, for_T=False, is_prefix_closed=False, is_suffix_closed=False))
    alphabet = system_sul.sul.alphabet
    sul = SystemDCSULST(M, system_sul)
    # print(B.execute_sequence(B.initial_state, ('C', 'C', 'B', 'D', 'C', 'C', 'C', 'B', 'D', 'C', 'B', 'D')))
    oracle = SystemDCOracleST(alphabet, sul, M, counter_examples_dict[example][t_type], walks_per_state=300,
                              walk_len=30, example=example, t_type=t_type)
    oracle = RandomWMethodEqOracle(alphabet, sul, counter_examples_dict[example][t_type], walks_per_state=300, walk_len=30)
    #oracle = RandomWalkEqOracle(alphabet, sul)
    #oracle = RandomWordEqOracle(alphabet, sul)


    dfa3, data = run_lsharp_square(alphabet,
                           sul,
                           oracle,
                           cache_and_non_det_check=False,
                           return_data=True)
    print(dfa3)


    data["ce_length"] = len(counter_examples_dict[example][t_type][0][1])
    data["alphabet_size"] = len(alphabet)
    data["T_size"] = len(M.states)
    data["B_size"] = 0
    data["system_steps"] = system_sul.sul.system_steps
    data["system_inits"] = system_sul.sul.system_inits
    data["system_steps_knowing_s"] = system_sul.sul.system_steps_knowing_s
    data["system_inits_knowing_s"] = system_sul.sul.system_inits_knowing_s
    return dfa3, data, M, []



def main_single(benchmark, t_type, method, description_type, early_detection):
    random.seed(0)
    example = benchmark  # "m183"  # "magento", "threads_example", "coffee", "coffee_new", "api_alice", "api_bob", "peterson", "m183"

    dfa3, data, M, B = run(example, t_type)
    # print(len(dfa3.states))
    # print(dfa3)

    if method == "solver":
        learner = FALearner(encoder=DFA3Encoder(dfa3, description_type, early_detection),
                            oracle=CompleteDFAOracle(dfa3.get_input_alphabet(), dfa3),
                            alphabet=dfa3.get_input_alphabet(),
                            max_states=len(dfa3.states),
                            use_all_traces=True,
                            binary_search=True,
                            minimize_self_loops=False,
                            verbose=True)

        start_time = int(time.time() * 1000) / 1000
        (dfa, statistics) = learn(learner, [])  # traces)
        end_time = int(time.time() * 1000) / 1000
    elif method == "rpni":
        rpni_results = {}
        for description_type in ["FE", "RC"]:
            for early_detection in [False, True]:
                current_dfa3 = deepcopy(dfa3)
                learner = RPNILearner(current_dfa3, data["observation_table"], description_type, early_detection)
                start_time = int(time.time() * 1000) / 1000
                dfa = learner.learn()
                end_time = int(time.time() * 1000) / 1000
                # print(description_type)
                # print(early_detection)
                # print(dfa)
                rpni_results[(description_type, early_detection)] = (end_time - start_time, len(dfa.states))

    from aalpy.utils import load_automaton_from_file
    from aalpy.automata import Dfa, DfaState
    from utils import minimize_dfa

    def moore_to_dfa(machine, accepting_output):
        d = {}
        for s in machine.states:
            d[s.state_id] = DfaState(s.state_id, is_accepting=s.output in accepting_output)
        for s in machine.states:
            for a, s2 in s.transitions.items():
                d[s.state_id].transitions[a] = d[s2.state_id]
        initial_state = d[machine.initial_state.state_id]
        return Dfa(initial_state, list(d.values()))

    b = moore_to_dfa(dfa3, "+")
    b = minimize_dfa(b)
    # print(b)

    t_s = moore_to_dfa(dfa3, "+-")
    t_s = minimize_dfa(t_s)


    # add to dict instead of printing
    results = {}
    results["benchmark"] = example
    # results["t_type"] = t_type
    results["ce_length"] = data["ce_length"]
    results["alphabet_size"] = data["alphabet_size"]
    results["T_size"] = data["T_size"]
    results["T_S_size"] = len(t_s.states)
    results["3DFA"] = data["automaton_size"]
    results["L* time"] = data["total_time"]
    results["system_inits"] = data["system_inits"]
    results["system_steps"] = data["system_steps"]
    results["system_inits_knowing_s"] = data["system_inits_knowing_s"]
    results["system_steps_knowing_s"] = data["system_steps_knowing_s"]
    results["B_size"] = len(b.states)
    # results["method"] = method
    max_time = 0
    for k, v in rpni_results.items():
        key_prefix = k[0]
        key_prefix += "_ED" if k[1] else ""
        key_prefix += "_"
        if v[0] > max_time:
            max_time = v[0]
        # results[key_prefix + "TIME"] = v[0]
        results[key_prefix + "DFA"] = v[1]
    results["L* time"] += max_time

    if t_type == "1":
        results = { col_name:results[col_name] for col_name in ["benchmark", "ce_length", "alphabet_size", "3DFA", "L* time", "FE_DFA", "B_size"]}
    elif t_type == "2":
        results = { col_name:results[col_name] for col_name in ["benchmark", "ce_length", "alphabet_size", "T_size", "3DFA", "L* time", "FE_DFA", "FE_ED_DFA", "B_size"]}
    else:
        results = {col_name: results[col_name] for col_name in ["benchmark", "ce_length", "alphabet_size", "3DFA", "L* time", "FE_DFA", "RC_DFA", "B_size"]}

    return results