# -*- coding: utf-8 -*-

""" Base classes for the pke module. """

from .readers import MinimalCoreNLPParser, PreProcessedTextReader, RawTextReader
from collections import defaultdict
from nltk.stem.snowball import SnowballStemmer as Stemmer
from nltk import RegexpParser
from string import punctuation
import os
import logging

from builtins import str

class Sentence(object):
    """ The sentence data structure. """

    def __init__(self, words):

        self.words = words
        """ tokens as a list. """

        self.pos = []
        """ Part-Of-Speeches as a list. """

        self.stems = []
        """ stems as a list. """

        self.length = len(words)
        """ length of the sentence. """

        self.meta = {}
        """ meta-information of the sentence. """


class Candidate(object):
    """ The keyphrase candidate data structure. """

    def __init__(self):

        self.surface_forms = []
        """ the surface forms of the candidate. """

        self.offsets = []
        """ the offsets of the surface forms. """

        self.sentence_ids = []
        """ the sentence id of each surface form. """

        self.pos_patterns = []
        """ the Part-Of-Speech patterns of the candidate. """

        self.lexical_form = []
        """ the lexical form of the candidate. """


class LoadFile(object):
    """ The LoadFile class that provides base functions. """

    def __init__(self, input_file=None, language='english'):
        """ Initializer for LoadFile class.

            Args:
                input_file (str): the path of the input file.
                language (str): the language of the input file (used for
                    stoplist), defaults to english.
        """

        self.input_file = input_file
        """ The path of the input file. """

        self.language = language
        """ The language of the input file. """

        self.sentences = []
        """ The sentence container (list of Sentence). """

        self.candidates = defaultdict(Candidate)
        """ The candidate container (dict of Candidate). """

        self.weights = {}
        """ The weight container (can be either word or candidate weights). """

        self._models = os.path.join(os.path.dirname(__file__), 'models')
        """ Root path of the pke module. """ 

        self._df_counts = os.path.join(self._models, "df-semeval2010.tsv.gz")
        """ Document frequency counts provided in pke. """


    def load_document(self,
                      input_file,
                      language='en',
                      format='raw'):
        """Loads the content of a document in a given format/language.

        Args:
            input_file (str): path to the input file.
            language (str): language of the input, defaults to 'en'.
            format (str): input format, defaults to 'raw'.
        """

        pass


    def load_text(self,
                  input_text,
                  language='en'):
        """Loads a text given as input.

        Args:
            input_text (str): input text.
            language (str): language of the input, defaults to 'en'.
        """

        pass


    def read_document(self,
                      format='raw',
                      use_lemmas=False,
                      stemmer='porter',
                      sep='/'):
        """ Read the input file in a given format.

            Args:
                format (str): the input format, defaults to raw.
                use_lemmas (bool): whether lemmas from stanford corenlp are used
                    instead of stems (computed by nltk), defaults to False.
                stemmer (str): the stemmer in nltk to use (if used), defaults
                    to porter (can be set to None for using word surface forms
                    instead of stems).
                sep (str): the separator of the tagged word, defaults to `/`.
        """

        if format == 'raw':
            self.read_raw_document(stemmer=stemmer)
        elif format == 'preprocessed':
            self.read_preprocessed_document(stemmer=stemmer, sep=sep)
        elif format == 'corenlp':
            self.read_corenlp_document(use_lemmas=use_lemmas, stemmer=stemmer)


    def read_text(self, input_text=None, stemmer='porter'):
        """ Read text as input.

            Args:
                input_text (str): the input text.
                stemmer (str): the stemmer in nltk to use, defaults to porter
                    (can be set to None for using word surface forms instead of
                    stems).
        """

        self.read_raw_document(stemmer=stemmer, input_text=input_text)


    def read_corenlp_document(self, use_lemmas=False, stemmer='porter'):
        """ Read the input file in CoreNLP XML format and populate the sentence
            list.

            Args:
                use_lemmas (bool): whether lemmas from stanford corenlp are used
                    instead of stems (computed by nltk), defaults to False.
                stemmer (str): the stemmer in nltk to use (if used), defaults
                    to porter (can be set to None for using word surface forms
                    instead of stems).
        """

        # parse the document using the Minimal CoreNLP parser
        parse = MinimalCoreNLPParser(self.input_file)

        self._populate_sentences(parse, stemmer=stemmer, use_lemmas=use_lemmas)

    def read_preprocessed_document(self, stemmer='porter', sep='/'):
        """ Read the preprocessed input file and populate the sentence list.

            Args:
                stemmer (str): the stemmer in nltk to use, defaults to porter
                    (can be set to None for using word surface forms instead of
                    stems).
                sep (str): the separator of the tagged word, defaults to /.
        """

        # parse the document using the preprocessed text parser
        parse = PreProcessedTextReader(self.input_file, sep=sep)

        self._populate_sentences(parse, stemmer=stemmer)

    def read_raw_document(self, stemmer='porter', input_text=None):
        """ Read the raw input file and populate the sentence list.

            Args:
                stemmer (str): the stemmer in nltk to use, defaults to porter
                    (can be set to None for using word surface forms instead of
                    stems).
                input_text (str): the text if directly given as input, defaults
                    to None (i.e. using an input file).
        """

        # parse the document using the preprocessed text parser
        parse = RawTextReader(path=self.input_file, input_text=input_text)

        self._populate_sentences(parse, stemmer=stemmer)

    def _populate_sentences(self, parsed_content, stemmer='porter', use_lemmas=False):
        """
            Populate the sentence list.
            Args:
                use_lemmas (bool): whether lemmas are used (if available)
                    instead of stems (computed by nltk), defaults to False.
                stemmer (str): the stemmer in nltk to use (if used), defaults
                    to porter (can be set to None for using word surface forms
                    instead of stems).
        """
        # loop through the parsed sentences
        for i, sentence in enumerate(parsed_content.sentences):

            # add the sentence to the container
            self.sentences.append(Sentence(words=sentence['words']))

            # add the POS
            self.sentences[i].pos = sentence['POS']

            if use_lemmas:
                # add the lemmas
                try:
                    self.sentences[i].stems = sentence['lemmas']
                except KeyError:
                    logging.error('Lemmas are not available in the chosen input format')
            else:
                if stemmer is not None:
                    # add the stems
                    stem = Stemmer(stemmer).stem
                    self.sentences[i] = [stem(word) for word in self.sentences[i].words]
                else:
                    # otherwise computations are performed on surface forms
                    self.sentences[i].stems = self.sentences[i].words

            # lowercase the stems/lemmas
            for j, stem in enumerate(self.sentences[i].stems):
                self.sentences[i].stems[j] = stem.lower()

            # add the meta-information
            # for k, infos in sentence.iteritems(): -- Python 2/3 compatible
            for (k, infos) in sentence.items():
                if k not in {'POS', 'lemmas', 'words'}:
                    self.sentences[i].meta[k] = infos


    def is_redundant(self, candidate, prev, mininum_length=1):
        """ Test if one candidate is redundant with respect to a list of already
            selected candidates. A candidate is considered redundant if it is
            included in another candidate that is ranked higher in the list.

            Args:
                candidate (str): the lexical form of the candidate.
                prev (list): the list of already selected candidates (lexical
                    forms).
                mininum_length (int): minimum length (in words) of the candidate
                    to be considered, defaults to 1.
        """

        # get the tokenized lexical form from the candidate
        candidate = self.candidates[candidate].lexical_form

        # only consider candidate greater than one word
        if len(candidate) < mininum_length:
            return False

        # get the tokenized lexical forms from the selected candidates
        prev = [self.candidates[u].lexical_form for u in prev]

        # loop through the already selected candidates
        for prev_candidate in  prev:
            for i in range(len(prev_candidate)-len(candidate)+1):
                if candidate == prev_candidate[i:i+len(candidate)]:
                    return True
        return False


    def get_n_best(self, n=10, redundancy_removal=False, stemming=False):
        """ Returns the n-best candidates given the weights.

            Args:
                n (int): the number of candidates, defaults to 10.
                redundancy_removal (bool): whether redundant keyphrases are
                    filtered out from the n-best list, defaults to False.
                stemming (bool): whether to extract stems or surface forms
                    (lowercased, first occurring form of candidate), default to
                    False.
        """

        # sort candidates by descending weight
        best = sorted(self.weights, key=self.weights.get, reverse=True)

        # remove redundant candidates
        if redundancy_removal:

            # initialize a new container for non redundant candidates
            non_redundant_best = []

            # loop through the best candidates
            for candidate in best:

                # test wether candidate is redundant
                if self.is_redundant(candidate, non_redundant_best):
                    continue

                # add the candidate otherwise
                non_redundant_best.append(candidate)

                # break computation if the n-best are found
                if len(non_redundant_best) >= n:
                    break

            # copy non redundant candidates in best container
            best = non_redundant_best

        # get the list of best candidates as (lexical form, weight) tuples
        n_best = [(u, self.weights[u]) for u in best[:min(n, len(best))]]

        # replace with surface forms if no stemming
        if not stemming:
            n_best = [(' '.join(self.candidates[u].surface_forms[0]).lower(),
                       self.weights[u]) for u in best[:min(n, len(best))]]

        if len(n_best) < n:
                logging.warning(
                        'Not enough candidates to choose from '
                        '({} requested, {} given)'.format(n, len(n_best)))

        # return the list of best candidates
        return n_best


    def add_candidate(self, words, stems, pos, offset, sentence_id):
        """ Add a keyphrase candidate to the candidates container.

            Args:
                words (list): the words (surface form) of the candidate.
                stems (list): the stemmed words of the candidate.
                pos (list): the Part-Of-Speeches of the words in the candidate.
                offset (int): the offset of the first word of the candidate.
                sentence_id (int): the sentence id of the candidate.
        """

        # build the lexical (canonical) form of the candidate using stems
        lexical_form = ' '.join(stems)

        # add/update the surface forms
        self.candidates[lexical_form].surface_forms.append(words)

        # add/update the lexical_form
        self.candidates[lexical_form].lexical_form = stems

        # add/update the POS patterns
        self.candidates[lexical_form].pos_patterns.append(pos)

        # add/update the offsets
        self.candidates[lexical_form].offsets.append(offset)

        # add/update the sentence ids
        self.candidates[lexical_form].sentence_ids.append(sentence_id)


    def ngram_selection(self, n=3):
        """ Select all the n-grams and populate the candidate container.

            Args:
                n (int): the n-gram length, defaults to 3.
        """

        # loop through the sentences
        for i, sentence in enumerate(self.sentences):

            # limit the maximum n for short sentence
            skip = min(n, sentence.length)

            # compute the offset shift for the sentence
            shift = sum([s.length for s in self.sentences[0:i]])

            # generate the ngrams
            for j in range(sentence.length):
                for k in range(j+1, min(j+1+skip, sentence.length+1)):

                    # add the ngram to the candidate container
                    self.add_candidate(words=sentence.words[j:k],
                                       stems=sentence.stems[j:k],
                                       pos=sentence.pos[j:k],
                                       offset=shift+j,
                                       sentence_id=i)

    def longest_pos_sequence_selection(self, valid_pos=None):
        self.longest_sequence_selection(
            key=lambda s: s.pos, valid_values=valid_pos)

    def longest_keyword_sequence_selection(self, keywords):
        self.longest_sequence_selection(
            key=lambda s: s.stem, valid_values=keywords)

    def longest_sequence_selection(self, key, valid_values):
        """ Select the longest sequences of given POS tags as candidates.

            Args:
                key (func) : function that given a sentence return an iterable
                valid_values (set): the set of valid values, defaults to None.
        """

        # loop through the sentences
        for i, sentence in enumerate(self.sentences):

            # compute the offset shift for the sentence
            shift = sum([s.length for s in self.sentences[0:i]])

            # container for the sequence (defined as list of offsets)
            seq = []

            # loop through the tokens
            for j, value in enumerate(key(self.sentences[i])):

                # add candidate offset in sequence and continue if not last word
                if value in valid_values:
                    seq.append(j)
                    if j < (sentence.length - 1):
                        continue

                # add sequence as candidate if non empty
                if seq:

                    # bias for candidate in last position within sentence
                    bias = 0
                    if j == (sentence.length - 1):
                        bias = 1

                    # add the ngram to the candidate container
                    self.add_candidate(words=sentence.words[seq[0]:seq[-1]+1],
                                       stems=sentence.stems[seq[0]:seq[-1]+1],
                                       pos=sentence.pos[seq[0]:seq[-1]+1],
                                       offset=shift+j-len(seq)+bias,
                                       sentence_id=i)

                # flush sequence container
                seq = []


    def grammar_selection(self, grammar=None):
        """ Select candidates using nltk RegexpParser with a grammar defining
            noun phrases (NP).

            Args:
                grammar (str): grammar defining POS patterns of NPs.
        """

        # initialize default grammar if none provided
        if grammar is None:
            grammar = r"""
                NBAR:
                    {<NN.*|JJ.*>*<NN.*>} 
                    
                NP:
                    {<NBAR>}
                    {<NBAR><IN><NBAR>}
            """

        # initialize chunker
        chunker = RegexpParser(grammar)

        # loop through the sentences
        for i, sentence in enumerate(self.sentences):

            # compute the offset shift for the sentence
            shift = sum([s.length for s in self.sentences[0:i]])

            # convert sentence as list of (offset, pos) tuples
            tuples = [(str(j), sentence.pos[j]) for j in range(sentence.length)]

            # parse sentence
            tree = chunker.parse(tuples)

            # find candidates
            for subtree in tree.subtrees():
                if subtree.label() == 'NP':
                    leaves = subtree.leaves()

                    # get the first and last offset of the current candidate
                    first = int(leaves[0][0])
                    last = int(leaves[-1][0])

                    # add the NP to the candidate container
                    self.add_candidate(words=sentence.words[first:last+1],
                                       stems=sentence.stems[first:last+1],
                                       pos=sentence.pos[first:last+1],
                                       offset=shift+first,
                                       sentence_id=i)


    def _is_alphanum(self, word, valid_punctuation_marks='-'):
        """Check if a word is valid, i.e. it contains only alpha-numeric
        characters and valid punctuation marks.

        Args:
            word (string): a word.
            valid_punctuation_marks (str): punctuation marks that are valid
                    for a candidate, defaults to '-'.
        """
        for punct in valid_punctuation_marks.split():
            word = word.replace(punct, '')
        return word.isalnum()


    def candidate_filtering(self,
                            stoplist=[],
                            mininum_length=3,
                            mininum_word_size=2,
                            valid_punctuation_marks='-',
                            maximum_word_number=5,
                            only_alphanum=True,
                            pos_blacklist=[]):
        """ Filter the candidates containing strings from the stoplist. Only
            keep the candidates containing alpha-numeric characters (if the
            non_latin_filter is set to True) and those length exceeds a given
            number of characters.
            
            Args:
                stoplist (list): list of strings, defaults to [].
                mininum_length (int): minimum number of characters for a
                    candidate, defaults to 3.
                mininum_word_size (int): minimum number of characters for a
                    token to be considered as a valid word, defaults to 2.
                valid_punctuation_marks (str): punctuation marks that are valid
                    for a candidate, defaults to '-'.
                maximum_word_number (int): maximum length in words of the
                    candidate, defaults to 5.
                only_alphanum (bool): filter candidates containing non (latin)
                    alpha-numeric characters, defaults to True.
                pos_blacklist (list): list of unwanted Part-Of-Speeches in
                    candidates, defaults to [].
        """

        # loop throught the candidates
        for k in list(self.candidates):

            # get the candidate
            v = self.candidates[k]

            # get the words from the first occurring surface form
            words = [u.lower() for u in v.surface_forms[0]]

            # discard if words are in the stoplist
            if set(words).intersection(stoplist):
                del self.candidates[k]

            # discard if tags are in the pos_blacklist
            elif set(v.pos_patterns[0]).intersection(pos_blacklist):
                del self.candidates[k]

            # discard if containing tokens composed of only punctuation
            elif any([set(u).issubset(set(punctuation)) for u in words]):
                del self.candidates[k]

            # discard candidates composed of 1-2 characters
            elif len(''.join(words)) < mininum_length:
                del self.candidates[k]

            # discard candidates containing small words (1-character)
            elif min([len(u) for u in words]) < mininum_word_size:
                del self.candidates[k]

            # discard candidates composed of more than 5 words
            elif len(v.lexical_form) > maximum_word_number:
                del self.candidates[k]

            # discard if not containing only alpha-numeric characters
            if only_alphanum and k in self.candidates:
                if not all([self._is_alphanum(w) for w in words]):
                    del self.candidates[k]

