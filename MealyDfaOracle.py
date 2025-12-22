# from aalpy.base import Automaton
# from aalpy.base.Oracle import Oracle
#
#
# class ValidityDataOracle(Oracle):
#     def __init__(self, automaton, missing):
#         """
#         Give data in format: [(["a", "b"], True), (["b", "a", "a"], False)]
#         """
#         self.automaton = automaton
#         self.missing = missing
#         self.num_queries = 0
#         self.num_steps = 0
#
#     def rec_equality(self, previous_state, current_state, hypothesis, word, seen):
#         if (previous_state, current_state) in self.missing:
#             return None
#         if (previous_state, current_state) in seen:
#             return None
#         seen.add((previous_state, current_state))
#         for next_state in current_state.transitions:
#             
#
#     def find_cex(self, hypothesis: Automaton):
#         for inputs, output in self.data:
#             hypothesis.reset_to_initial()
#             for input_val in inputs:
#                 hypothesis.step(input_val)
#                 self.num_steps += 1
#             hyp_output = hypothesis.step(None)
#             self.num_queries += 1
#             if hyp_output != output:
#                 return inputs
#         return None