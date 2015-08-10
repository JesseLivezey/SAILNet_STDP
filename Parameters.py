# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 15:28:32 2015

@author: Bernal
"""
import ConfigParser
import numpy as np
import theano

class Parameters():
    
    def __init__(self,parameters_file):
        config = ConfigParser.ConfigParser()
        config.read(parameters_file)
        rng = np.random.RandomState(0)
        
        """
        Load network Parameters from config file
        """
        
        self.rule = config.get('LearningRule','dW_rule')
        self.function = config.get('LearningRule','function')

        self.batch_size = config.getint("Parameters",'batch_size')
        self.num_trials = config.getint("Parameters",'num_trials')
        self.num_iterations = config.getint("Parameters",'num_iterations')
        self.reduced_learning_rate = np.array(config.getfloat("Parameters",'reduced_learning_rate')).astype('float32')
        self.N = config.getint("NeuronParameters",'N')
        self.OC = config.getint("NeuronParameters",'OC')
        self.p = config.getfloat("NeuronParameters",'p')
        self.alpha = theano.shared(np.array(config.getfloat("LearningRates",'alpha')).astype('float32'))
        self.beta = theano.shared(np.array(config.getfloat("LearningRates",'beta')).astype('float32'))
        self.gamma = theano.shared(np.array(config.getfloat("LearningRates",'gamma')).astype('float32'))
        self.eta_ave = config.getfloat("LearningRates",'eta_ave')
        self.lateral_constraint = config.getfloat('LearningRates','lateral_constraint')
        self.M = self.OC*self.N        
        self.Q = rng.randn(self.N,self.M)
        
        
