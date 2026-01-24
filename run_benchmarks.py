import concurrent.futures
import datetime
import logging
import os
import random
from typing import Any

import aalpy
from aalpy.oracles.PerfectKnowledgeEqOracle import PerfectKnowledgeEqOracle

from IncompleteDfaSUL import IncompleteDfaSUL
from LSharpSquare import run_lsharp_square
from MealyDfaOracle import MealyDfaOracle
from ValidityDataOracle import ValidityDataOracle

test_cases_path = "benchmarking/benchmarks/"
logging.basicConfig(level=logging.INFO, format=f"%(asctime)s %(levelname)s: %(message)s", datefmt="%H:%M:%S")


def is_simple_input(inp: str) -> bool:
    return all(c in ["0", "1", "X"] for c in inp)


def get_possible_words(prefix: str, suffix: str, alphabet: list) -> list:
    words = []
    if suffix:
        if suffix[0] == "X":
            for letter in alphabet:
                words.extend(get_possible_words(prefix + letter, suffix[1:], alphabet))
        else:
            letter = suffix[0]
            words.extend(get_possible_words(prefix + letter, suffix[1:], alphabet))
        return words
    else:
        return [prefix]


def parse_file(filename: str, alphabet: list, horizon: int | None = None) -> tuple[list, list]:
    with open(test_cases_path + filename, 'r') as f:
        known_words = []
        observed_alphabet = []
        for l in f:
            split_index = l.strip().rfind(',')
            inp = l.strip()[:split_index]
            out = l.strip()[split_index + 1:]
            out = out.strip() == "+"
            if is_simple_input(inp):
                inputs = get_possible_words("", inp, alphabet)
                for word in inputs:
                    for letter in word:
                        if not letter in observed_alphabet:
                            observed_alphabet.append(letter)
                    known_words.append((word, out))
            else:
                word = inp.split(";")
                for letter in word:
                    if not letter in observed_alphabet:
                        observed_alphabet.append(letter)
                if horizon is None or len(word) <= horizon:
                    known_words.append((word, out))

        return known_words, observed_alphabet


def run_test_case(filename: str, solver_timeout, replace_basis, use_compatibility, horizon: int | None = None) -> dict[
    str, Any]:
    alphabet = [True, False]
    data, alphabet = parse_file(filename, alphabet, horizon)
    sul = IncompleteDfaSUL(data.copy())
    eq_oracle = ValidityDataOracle(data.copy())

    learned_dfa, info = run_lsharp_square(alphabet, sul, eq_oracle, return_data=True, solver_timeout=solver_timeout,
                                          replace_basis=replace_basis, use_compatibility=use_compatibility)

    successful = learned_dfa is not None and eq_oracle.find_cex(learned_dfa) is None
    info["successful"] = successful
    return info


def process_file(file_name: str, target_folder: str, solver_timeout, replace_basis, use_compatibility) -> str:
    logging.info(f"Testing {file_name}")
    info = run_test_case(f"{target_folder}/{file_name}", solver_timeout, replace_basis, use_compatibility)
    row = ','.join([f"{target_folder}/{file_name}", str(info['successful']), str(info['learning_rounds']),
                    str(info['automaton_size']), str(info['learning_time']), str(info['smt_time']),
                    str(info['eq_oracle_time']), str(info['total_time']), str(info['queries_learning']),
                    str(info['validity_query']), str(info['nodes']), str(info['informative_nodes']),
                    str(info['sul_steps']), str(info['queries_eq_oracle']), str(info['steps_eq_oracle'])]) + "\n"
    logging.info(f"Finished testing {file_name}")
    logging.info(f"Time: {info['total_time']}")
    logging.info(f"Queries: {info['queries_learning']}")
    logging.info(f"Validity: {info['validity_query']}")
    logging.info(f"Size: {info['automaton_size']}")
    return row


def run_test_cases_pool(file: str, extension: str, solver_timeout, replace_basis, use_compatibility) -> None:
    with open(f"benchmarking/results/benchmark{extension}_{file}.csv", "w") as f:
        f.write("file name,succeeded,learning_rounds,automaton_size,learning_time,"
                "smt_time,eq_oracle_time,total_time,queries_learning,validity_query,nodes,"
                "informative_nodes,sul_steps,queries_eq_oracle,steps_eq_oracle\n")
        oliveira = test_cases_path
        target_folder = file
        folder_path = os.path.join(oliveira, target_folder)
        file_names = sorted(os.listdir(folder_path))

        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = list(executor.map(process_file, file_names, [target_folder] * len(file_names),
                                        [solver_timeout] * len(file_names), [replace_basis] * len(file_names),
                                        [use_compatibility] * len(file_names)))
            for row in results:
                f.write(row)


def run_mealy_benchmarks(file: str, solver_timeout, replace_basis, use_compatibility) -> None:
    from MealyDfaSUL import MealyDfaSUL
    mealy = aalpy.load_automaton_from_file(file, automaton_type="mealy")
    triples = []
    for state1 in mealy.states:
        for input1, state2 in state1.transitions.items():
            for input2, state3 in state2.transitions.items():
                triples.append((state1, input1, input2))
    max_missing = len(triples)
    missing = set()
    # print(max_missing)
    sul = MealyDfaSUL(mealy, list(missing))
    input_alphabet = mealy.get_input_alphabet()
    output_alphabet = set()
    for state in mealy.states:
        for output in state.output_fun.values():
            output_alphabet.add(output)
    alphabet = list(set(input_alphabet + list(output_alphabet)))
    oracle = MealyDfaOracle(mealy, sul.missing)
    learned_mealy, info = run_lsharp_square(alphabet, sul, oracle, return_data=True, solver_timeout=solver_timeout,
                                            replace_basis=replace_basis, use_compatibility=use_compatibility)
    # print(info)
    # print(f"file_name,missing_transitions," + ",".join([k for k,v in info.items()]))
    print(f"{len(missing)}," + ",".join([str(info[k]) for k,v in info.items()]))
    number_of_states = learned_mealy.size if learned_mealy is not None else 0
    # number_of_state_list = [number_of_states]
    dfa_oracle = PerfectKnowledgeEqOracle(alphabet, None, learned_mealy)

    # Learn mealy machines with increasing number of missing transitions
    num_fails = 0
    increase = 5
    i = increase
    while i <= max_missing:
        number_missing = i
        mealy = aalpy.load_automaton_from_file(file, automaton_type="mealy")
        mealy_states = len(mealy.states)
        triples = []
        for state1 in mealy.states:
            for input1, state2 in state1.transitions.items():
                for input2, state3 in state2.transitions.items():
                    triples.append((state1, input1, input2))
        missing = random.sample(triples, min(number_missing, len(triples)))
        sul = MealyDfaSUL(mealy, list(missing))
        oracle = MealyDfaOracle(mealy, sul.missing)
        learned_mealy, info = run_lsharp_square(alphabet, sul, oracle, return_data=True, solver_timeout=solver_timeout,
                                                replace_basis=replace_basis, use_compatibility=use_compatibility)
        # print(info)
        # number_of_states = learned_mealy.size if learned_mealy is not None else 0
        # number_of_state_list.append(number_of_states)
        cex = dfa_oracle.find_cex(learned_mealy)
        if cex is not None:
            num_fails += 1
            if num_fails >= 3:
                return
        else:
            num_fails = 0
            i += increase
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            # print(f"{current_time},{mealy_states},{number_missing}")
            values = info.items()
            print(f"{len(missing)}," + ",".join([str(info[k]) for k,v in values]))

def main() -> None:
    solver_timeout = 2000000
    replace_basis = False
    use_compatibility = False
    # Redirect stdout to results.csv


    # run_test_cases_pool("all", f"2_t{solver_timeout}_r{replace_basis}_c{use_compatibility}", solver_timeout,
    #                     replace_basis, use_compatibility)
    models_folder = "benchmarking/models"
    if not os.path.isdir(models_folder):
        logging.error(f"Models folder not found: {models_folder}")
        return

    # file_names = sorted([f for f in os.listdir(models_folder) if os.path.isfile(os.path.join(models_folder, f))])[:1]
    file_names = ["OpenSSL_1.0.2_client_regular.dot"] * 16
    if not file_names:
        logging.info(f"No model files found in {models_folder}")
        return

    file_paths = [os.path.join(models_folder, f) for f in file_names]

    logging.info(f"Running Mealy benchmarks on {len(file_paths)} files in {models_folder}")
    print("missing_transitions,learning_rounds,automaton_size,learning_time,smt_time,eq_oracle_time,total_time,queries_learning,successful_queries_learning,validity_query,nodes,informative_nodes,sul_steps,cache_saved,queries_eq_oracle,steps_eq_oracle")
    # run_mealy_benchmarks(file_paths[0], solver_timeout, replace_basis, use_compatibility)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(run_mealy_benchmarks,
                     file_paths,
                     [solver_timeout] * len(file_paths),
                     [replace_basis] * len(file_paths),
                     [use_compatibility] * len(file_paths))
    logging.info("Mealy benchmarks complete")

    # solver_timeout = 200
    # replace_basis = True
    # use_compatibility = True
    # run_test_cases_pool("all", f"2_t{solver_timeout}_r{replace_basis}_c{use_compatibility}", solver_timeout, replace_basis, use_compatibility)
    #
    # solver_timeout = 200
    # replace_basis = True
    # use_compatibility = True
    # run_test_cases_pool("all", f"_t{solver_timeout}_r{replace_basis}_c{use_compatibility}", solver_timeout, replace_basis, use_compatibility)
    #
    # solver_timeout = 60
    # replace_basis = True
    # use_compatibility = False
    # run_test_cases_pool("all", f"_t{solver_timeout}_r{replace_basis}_c{use_compatibility}", solver_timeout, replace_basis, use_compatibility)
    return


if __name__ == "__main__":
    main()
