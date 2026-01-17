from aalpy import Oracle
from aalpy.base import Automaton


class MealyDfaOracle(Oracle):
    def __init__(self, automaton, missing):
        super().__init__(None, None)
        self.automaton = automaton
        self.missing = missing
        self.num_queries = 0
        self.num_steps = 0

    def rec_equality(self, mealy_state, hypothesis_state, hypothesis, word, seen):
        if (mealy_state.state_id, hypothesis_state.state_id) in seen:
            return None
        seen.add((mealy_state.state_id, hypothesis_state.state_id))
        for inp, next_state in mealy_state.transitions.items():
            if (mealy_state.state_id, next_state.state_id) in self.missing:
                continue
            output = mealy_state.output_fun[inp]
            # Taking the input and then the output transition should lead to a true state in hypothesis
            hyp_next1 = hypothesis_state.transitions[inp]
            # Odd lengths are rejecting
            if hyp_next1.is_accepting:
                return word + [inp]
            hyp_next2 = hyp_next1.transitions[output]
            if not hyp_next2.is_accepting:
                return word + [inp, output]
            # Recur further
            cex = self.rec_equality(next_state, hyp_next2, hypothesis, word + [inp, output], seen)
            if cex is not None:
                return cex
            # All others should have a false output
            for output2, hyp_next_state in hyp_next1.transitions.items():
                if output2 != output:
                    if hyp_next_state.is_accepting:
                        return word + [inp, output2]
        return None

    def find_cex(self, hypothesis: Automaton):
        cex = self.rec_equality(self.automaton.initial_state, hypothesis.initial_state, hypothesis, [], set())
        return cex
