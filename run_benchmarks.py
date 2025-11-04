import concurrent.futures
import datetime
import logging
import os
from typing import Any

from IncompleteDfaSUL import IncompleteDfaSUL
from LSharpSquare import run_lsharp_square
from ValidityDataOracle import ValidityDataOracle
from NoisyDfaSUL import NoisyDfaSUL

from aalpy.oracles.PerfectKnowledgeEqOracle import PerfectKnowledgeEqOracle
from aalpy.utils import generate_random_dfa

# From the Aalpy folder, run using:
# PYTHONPATH=. python3 Benchmarking/incomplete_dfa_benchmark/benchmark_incomplete_dfa.py

test_cases_path = "benchmarking/benchmarks/"
logging.basicConfig(level=logging.INFO, format=f"%(asctime)s %(levelname)s: %(message)s", datefmt="%H:%M:%S")


def is_simple_input(inp: str) -> bool:
    return all(c in ["0", "1", "X"] for c in inp)


def test_random_dfa(size: int, error_rate: float, alphabet: list) -> Any:
    dfa = generate_random_dfa(size, alphabet)
    sul = NoisyDfaSUL(dfa, error_rate)
    oracle = PerfectKnowledgeEqOracle(alphabet, sul, dfa)
    learned_dfa, info = run_lsharp_square(alphabet, sul, oracle, return_data=True)
    successful = learned_dfa is not None and oracle.find_cex(learned_dfa) is None
    info["successful"] = successful
    print(info)
    return None

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


def run_test_case(filename: str, solver_timeout, replace_basis, use_compatibility, horizon: int | None = None) -> dict[str, Any]:
    alphabet = [True, False]
    data, alphabet = parse_file(filename, alphabet, horizon)
    sul = IncompleteDfaSUL(data.copy())
    eq_oracle = ValidityDataOracle(data.copy())

    learned_dfa, info = run_lsharp_square(alphabet, sul, eq_oracle, return_data=True, solver_timeout=solver_timeout, replace_basis=replace_basis, use_compatibility=use_compatibility)

    successful = learned_dfa is not None and eq_oracle.find_cex(learned_dfa) is None
    info["successful"] = successful
    return info


def run_test_case_horizon_increase(file_name: str, max_horizon: int | None = None) -> None:
    with open(f"benchmarking/results/benchmark_{file_name.replace('/', '_')}.csv", "w") as f:
        f.write("horizon,file_name,succeeded,learning_rounds,automaton_size,learning_time,"
                "smt_time,eq_oracle_time,total_time,queries_learning,validity_query,nodes,"
                "informative_nodes,sul_steps,queries_eq_oracle,steps_eq_oracle\n")

        for horizon in range(1, max_horizon + 1):
            logging.info(f"Testing {file_name} with horizon={horizon}")
            info = run_test_case(f"AAL-benchmarks/{file_name}", horizon=horizon)
            f.write(','.join([str(horizon),
                              file_name,
                              str(info['successful']),
                              str(info['learning_rounds']),
                              str(info['automaton_size']),
                              str(info['learning_time']),
                              str(info['smt_time']),
                              str(info['eq_oracle_time']),
                              str(info['total_time']),
                              str(info['queries_learning']),
                              str(info['validity_query']),
                              str(info['nodes']),
                              str(info['informative_nodes']),
                              str(info['sul_steps']),
                              str(info['queries_eq_oracle']),
                              str(info['steps_eq_oracle'])]) + "\n")
            logging.info(f"Finished testing {file_name}")
            logging.info(f"Time: {info['total_time']}")
            logging.info(f"Queries: {info['queries_learning']}")
            logging.info(f"Validity: {info['validity_query']}")
            logging.info(f"Size: {info['automaton_size']}")
            if not info['successful']:
                break


def process_file(file_name: str, target_folder: str, solver_timeout, replace_basis, use_compatibility) -> str:
    logging.info(f"Testing {file_name}")
    info = run_test_case(f"{target_folder}/{file_name}", solver_timeout, replace_basis, use_compatibility)
    row = ','.join([f"{target_folder}/{file_name}",
                    str(info['successful']),
                    str(info['learning_rounds']),
                    str(info['automaton_size']),
                    str(info['learning_time']),
                    str(info['smt_time']),
                    str(info['eq_oracle_time']),
                    str(info['total_time']),
                    str(info['queries_learning']),
                    str(info['validity_query']),
                    str(info['nodes']),
                    str(info['informative_nodes']),
                    str(info['sul_steps']),
                    str(info['queries_eq_oracle']),
                    str(info['steps_eq_oracle'])]) + "\n"
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
            results = list(executor.map(process_file, file_names, [target_folder] * len(file_names), [solver_timeout] * len(file_names),[replace_basis] * len(file_names), [use_compatibility] * len(file_names)))
            for row in results:
                f.write(row)


def main() -> None:
    # test_random_dfa(50, 0.9, ["a", "b"])
    solver_timeout = 200
    replace_basis = True
    use_compatibility = False
    run_test_cases_pool("all", f"_t{solver_timeout}_r{replace_basis}_c{use_compatibility}", solver_timeout, replace_basis, use_compatibility)

    solver_timeout = 200
    replace_basis = False
    use_compatibility = False
    run_test_cases_pool("all", f"_t{solver_timeout}_r{replace_basis}_c{use_compatibility}", solver_timeout, replace_basis, use_compatibility)

    solver_timeout = 200
    replace_basis = True
    use_compatibility = True
    run_test_cases_pool("all", f"_t{solver_timeout}_r{replace_basis}_c{use_compatibility}", solver_timeout, replace_basis, use_compatibility)

    solver_timeout = 60
    replace_basis = True
    use_compatibility = False
    run_test_cases_pool("all", f"_t{solver_timeout}_r{replace_basis}_c{use_compatibility}", solver_timeout, replace_basis, use_compatibility)
    return

if __name__ == "__main__":
    main()