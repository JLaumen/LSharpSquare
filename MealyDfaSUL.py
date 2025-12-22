from CacheTree import CacheTree
from aalpy.automata import Dfa, MealyMachine, MealyState
from aalpy.base.SUL import SUL
from random import random


class MealyDfaSUL(SUL):
    def __init__(self, automaton: MealyMachine, missing: list):
        super().__init__()
        self.automaton: MealyMachine = automaton
        self.num_unsuccesful_queries = 0
        self.missing = set()

        for state1, state2, state3 in missing:
            input_to_2 = [k for k, v in state1.transitions.items() if v == state2][0]
            input_to_3 = [k for k, v in state2.transitions.items() if v == state3][0]
            # Create new state, redirect first transition to it
            new_state = MealyState(f"missing_{len(self.missing)}")
            state1.transitions[input_to_2] = new_state
            # Copy outputs and transitions from state2 to new_state
            for inp, tgt in state2.transitions.items():
                new_state.transitions[inp] = tgt
                new_state.output_fun[inp] = state2.output_fun[inp]
            automaton.states.append(new_state)
            self.missing.add((new_state, state3))

    def pre(self):
        self.automaton.reset_to_initial()

    def step(self, letter=None):
        pass

    def post(self):
        pass

    def query(self, word: tuple):
        """
        Performs a membership query on the SUL. Before the query, pre() method is called and after the query post()
        method is called. Each letter in the word (input in the input sequence) is executed using the step method.

        Args:

            word: membership query (word consisting of letters/inputs)

        Returns:

            final output

        """
        self.pre()
        self.num_queries += 1
        self.num_steps += len(word)

        if len(word) % 2 == 1:
            return False

        current_state = self.automaton.initial_state

        for i in range(0, len(word), 2):
            input_letter = word[i]
            expected_output = word[i + 1]
            if input_letter not in self.automaton.get_input_alphabet():
                return False
            actual_output = self.automaton.step(input_letter)
            previous_state = current_state
            current_state = self.automaton.current_state
            if actual_output != expected_output:
                if (previous_state, current_state) in self.missing:
                    return "unknown"
                return False

        # print("True query:", word)
        return True