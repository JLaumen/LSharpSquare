from aalpy.automata import MealyMachine, MealyState
from aalpy.base.SUL import SUL


class MealyDfaSUL(SUL):
    def __init__(self, automaton: MealyMachine, missing: list):
        super().__init__()
        self.automaton: MealyMachine = automaton
        self.num_successful_queries = 0
        self.missing = set()
        extra_states = dict()

        for state1, input_to_2, input_to_3 in missing:
            if extra_states.get((state1.state_id, input_to_2)) is None:
                state2 = state1.transitions[input_to_2]
                state3 = state2.transitions[input_to_3]
                # Create new state, redirect first transition to it
                new_state = MealyState(f"missing_{len(self.missing)}")
                extra_states[(state1.state_id, input_to_2)] = new_state
                state1.transitions[input_to_2] = new_state
                # Copy outputs and transitions from state2 to new_state
                for inp, tgt in state2.transitions.items():
                    new_state.transitions[inp] = tgt
                    new_state.output_fun[inp] = state2.output_fun[inp]
                automaton.states.append(new_state)
            else:
                state2 = state1.transitions[input_to_2]
                state3 = state2.transitions[input_to_3]
                new_state = extra_states[(state1.state_id, input_to_2)]
            self.missing.add((new_state.state_id, state3.state_id))

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
        self.num_successful_queries += 1
        self.num_steps += len(word)

        if len(word) % 2 == 1:
            return False

        current_state = self.automaton.initial_state.state_id

        for i in range(0, len(word), 2):
            input_letter = word[i]
            expected_output = word[i + 1]
            if input_letter not in self.automaton.get_input_alphabet():
                return False
            actual_output = self.automaton.step(input_letter)
            previous_state = current_state
            current_state = self.automaton.current_state.state_id
            if (previous_state, current_state) in self.missing:
                self.num_successful_queries -= 1
                return "unknown"
            if actual_output != expected_output:
                return False

        return True
