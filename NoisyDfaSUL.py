from CacheTree import CacheTree
from aalpy.automata import Dfa
from aalpy.base.SUL import SUL
from random import random


class NoisyDfaSUL(SUL):
    def __init__(self, automaton: Dfa, error_rate: float):
        super().__init__()
        self.automaton: Dfa = automaton
        self.words = set()
        self.error_rate = error_rate
        self.num_unsuccesful_queries = 0

    def pre(self):
        self.automaton.reset_to_initial()
        self.last_output = self.automaton.step(None)

    def step(self, letter=None):
        self.last_output = self.automaton.step(letter)

    def post(self):
        return self.last_output

    def query(self, word: tuple) -> list:
        """
        Performs a membership query on the SUL. Before the query, pre() method is called and after the query post()
        method is called. Each letter in the word (input in the input sequence) is executed using the step method.

        Args:

            word: membership query (word consisting of letters/inputs)

        Returns:

            final output

        """
        if "".join(word) in self.words:
            self.num_queries += 1
            return "unknown"
        self.pre()
        # Empty string for DFA
        for letter in word:
            self.step(letter)
        out = self.post()
        # print("query:", word, out)
        self.num_queries += 1
        self.num_steps += len(word)
        if out == "unknown":
            self.num_unsuccesful_queries += 1
        # Return unknown with a probability error_rate
        if random() < self.error_rate:
            self.words.add("".join(word))
            return "unknown"

        return out
