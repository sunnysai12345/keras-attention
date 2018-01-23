import json
import csv
import random
import operator

import numpy as np
import pandas as pd
from keras.utils.np_utils import to_categorical
from keras.preprocessing.text import Tokenizer
from nltk.tokenize import word_tokenize


random.seed(1984)

INPUT_PADDING = 50
OUTPUT_PADDING = 100


class Vocabulary(object):

    def __init__(self, vocabulary_file, padding=None):
        """
            Creates a vocabulary from a file
            :param vocabulary_file: the path to the vocabulary
        """
        self.vocabulary_file = vocabulary_file
        with open(vocabulary_file, 'r',encoding='utf-8') as f:
            self.vocabulary = json.load(f)

        self.padding = padding
        self.reverse_vocabulary = {v: k for k, v in self.vocabulary.items()}

    def size(self):
        """
            Gets the size of the vocabulary
        """
        return len(self.vocabulary.keys())

    def string_to_int(self, text):
        """
            Converts a string into it's character integer 
            representation
            :param text: text to convert
        """
        tokens = word_tokenize(text)

        integers = []

        if self.padding and len(tokens) >= self.padding:
            # truncate if too long
            tokens = tokens[:self.padding - 1]

        tokens.append('<eos>')

        for c in tokens:
            if c in self.vocabulary:
                integers.append(self.vocabulary[c])
            else:
                integers.append(self.vocabulary['<unk>'])


        # pad:
        if self.padding and len(integers) < self.padding:
            integers.reverse()
            integers.extend([self.vocabulary['<unk>']]
                            * (self.padding - len(integers)))
            integers.reverse()

        if len(integers) != self.padding:
            print(text)
            raise AttributeError('Length of text was not padding.')
        return integers

    def int_to_string(self, integers):
        """
            Decodes a list of integers
            into it's string representation
        """
        tokens = []
        for i in integers:
            tokens.append(self.reverse_vocabulary[i])

        return tokens


class Data(object):

    def __init__(self, file_name, input_vocabulary, output_vocabulary,kb_vocabulary):
        """
            Creates an object that gets data from a file
            :param file_name: name of the file to read from
            :param vocabulary: the Vocabulary object to use
            :param batch_size: the number of datapoints to return
            :param padding: the amount of padding to apply to 
                            a short string
        """

        self.input_vocabulary = input_vocabulary
        self.output_vocabulary = output_vocabulary
        self.kb_vocabulary=kb_vocabulary
        self.kbfile = "./data/normalised_kbtuples.csv"
        self.file_name = file_name
    def kb_out(self):
        df=pd.read_csv(self.kbfile)
        self.kbs=list(df["subject"]+" "+df["relation"])
        self.kbs = np.array(list(
            map(self.kb_vocabulary.string_to_int, self.kbs)))
        #print(type(self.kbs),self.kbs,self.kbs.shape)
        #return self.kbs

    def load(self):
        """
            Loads data from a file
        """
        self.inputs = []
        self.targets = []

        with open(self.file_name, 'r',encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                self.inputs.append(row[1])
                self.targets.append(row[2])


    def transform(self):
        """
            Transforms the data as necessary
        """
        # @TODO: use `pool.map_async` here?
        self.inputs = np.array(list(
            map(self.input_vocabulary.string_to_int, self.inputs)))
        self.targets = np.array(list(map(self.output_vocabulary.string_to_int, self.targets)))
        #self.targets1 = np.array(list(map(self.kb_vocabulary.string_to_int, self.targets1)))
        '''x=list(map(
                lambda x: to_categorical(
                    x,
                    num_classes=self.output_vocabulary.size()+1),
                self.targets))
        self.targets = np.array(x)'''
        #print(self.inputs.shape,self.targets.shape)
        #assert len(self.inputs.shape) == 2, 'Inputs could not properly be encoded'
        #assert len(self.targets.shape) == 3, 'Targets could not properly be encoded'

    def generator(self, batch_size):
        """
            Creates a generator that can be used in `model.fit_generator()`
            Batches are generated randomly.
            :param batch_size: the number of instances to include per batch
        """
        instance_id = range(len(self.inputs))
        while True:
            try:
                batch_ids = random.sample(instance_id, batch_size)
                targets=np.array(self.targets[batch_ids])
                targets = np.array(list(map(lambda x: to_categorical(x,num_classes=self.output_vocabulary.size()),targets)))
                #print(self.inputs.shape,self.inputs[0],np.repeat(self.kbs[np.newaxis,:,:],batch_size,axis=0).shape,np.array(self.inputs[batch_ids], dtype=int).shape)
                yield ([np.array(self.inputs[batch_ids], dtype=int),np.repeat(self.kbs[np.newaxis,:,:],batch_size,axis=0)],np.array(targets))
            except Exception as e:
                print('EXCEPTION OMG')
                print(e)
                yield None, None,None

if __name__ == '__main__':
    input_vocab = Vocabulary('./data/vocabulary_drive.json', padding=40)
    output_vocab = Vocabulary('./data/vocabulary_drive.json', padding=40)
    kb_vocabulary = Vocabulary('./data/vocabulary_drive.json', padding=4)
    ds = Data('./data/training_drive.csv', input_vocab, output_vocab,kb_vocabulary)
    ds.kb_out()
    g = ds.generator(32)
    ds.load()
    ds.transform()
    #print(ds.targets.shape)
    '''print(ds.inputs.shape)
    print(ds.targets.shape)
    print(ds.targets[0])
    print(ds.inputs[[5,10, 12]].shape)
    print(ds.targets[[5,10,12]].shape)'''
    for i in range(50):
         print(next(g)[1].shape)
         print(output_vocab.int_to_string(list(next(g)[0])))
         print(output_vocab.int_to_string(list(next(g)[1])))
         break
